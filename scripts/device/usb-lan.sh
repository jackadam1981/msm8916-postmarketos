#!/bin/sh
# usb-lan.sh -- expose the dongle as an RNDIS Ethernet gadget on 192.168.100.1
#
# Why this exists
# ---------------
# The gadget inherited from the pmOS initramfs advertised
#   functions/rndis.usb0/{class,subclass,protocol} = 02/06/00
# which is the CDC-ECM triple. Windows has no inbox driver for ECM, so the
# dongle landed on Code 28 ("no driver installed") and never came up.
#
# Stock Android dongles/phones "just work" on Windows because their gadget
# does two extra things:
#   1. reports the RNDIS-mandated triple E0/01/03 (Wireless / RF / RNDIS)
#   2. publishes Microsoft OS descriptors with compatible_id=RNDIS and
#      sub_compatible_id=5162001, so the host matches USB\MS_COMP_RNDIS and
#      auto-binds usb8023.sys with no manual driver install.
# This script reproduces exactly that, then brings up the LAN side:
#   usb0 = 192.168.100.1/24, dnsmasq DHCP .10-.100, NAT out via wwan*.
#
# 172.16.42.1/16 is kept as a secondary address: it is what the pmOS
# initramfs uses for its SSH/telnet fallback, so recovery stays possible even
# if DHCP on the host is broken.
#
# MAC addresses
# -------------
# The UFI003 family is many identical sticks, so a hardcoded MAC makes every
# second unit plugged into the same host collide. Derive it from the board
# serial instead, using the same rule wcn36xx already applies to wlan0:
#
#   serial-number 26e041bc  ->  wlan0  02:00:26:e0:41:bc
#                               usb0   02:00:26:e0:41:be   (base + 2)
#                               host   02:00:26:e0:41:bf   (base + 3)
#
# +2/+3 keeps us off wlan0's address; two interfaces sharing a MAC makes the
# host's ARP table flap. The offsets are part of the on-wire identity, so do
# not renumber them casually -- hosts key DHCP leases off these.
#
# There is no per-unit MAC in this family's NV: /persist ships
# WCNSS_qcom_wlan_nv.bin (a 2022 generic calibration template, no 5ca0 OUI
# anywhere in it) plus a template .bt_nv.bin. The serial is the only stable
# per-unit value available, which is why wcn36xx falls back to it too.
#
# Override per unit by dropping /etc/usb-lan/mac.conf containing:
#   DEV_MAC=02:00:xx:xx:xx:xx
#   HOST_MAC=02:00:xx:xx:xx:xx
#
# Usage: usb-lan.sh up | down | status

set -eu

GADGET=/sys/kernel/config/usb_gadget/g1
UDC_NAME=${UDC_NAME:-ci_hdrc.0}

LAN_IP=192.168.100.1
LAN_PREFIX=24
LAN_NET=192.168.100.0/24
LEGACY_IP=172.16.42.1

MAC_CONF=/etc/usb-lan/mac.conf
DEV_MAC=
HOST_MAC=
SERIAL_NUM=

DNSMASQ_CONF=/etc/usb-lan/dnsmasq.conf
PIDFILE=/run/usb-lan-dnsmasq.pid

log() { echo "[usb-lan] $*"; }

# Fill DEV_MAC / HOST_MAC. Order of precedence:
#   1. /etc/usb-lan/mac.conf  (per-unit override)
#   2. board serial number    (same rule as wcn36xx, see header)
#   3. hardcoded pair         (last resort; logs a warning)
resolve_macs() {
    SERIAL_NUM=$(tr -d '\000 \n\t' < /sys/firmware/devicetree/base/serial-number 2>/dev/null || true)

    if [ -f "$MAC_CONF" ]; then
        # shellcheck disable=SC1090
        . "$MAC_CONF"
        log "MAC from $MAC_CONF: dev=$DEV_MAC host=$HOST_MAC"
    fi

    if [ -z "$DEV_MAC" ] || [ -z "$HOST_MAC" ]; then
        case "$SERIAL_NUM" in
            ''|*[!0-9a-fA-F]*)
                log "WARN: serial-number missing or not hex ('$SERIAL_NUM'), using built-in MACs"
                ;;
            *)
                # Serials in this family are not all the same width -- the
                # inventory has 26e041bc but also 1db15d2. Left-pad to 8 hex
                # digits so the derivation stays positional and stable.
                while [ "${#SERIAL_NUM}" -lt 8 ]; do SERIAL_NUM="0$SERIAL_NUM"; done
                if [ "${#SERIAL_NUM}" -gt 8 ]; then
                    log "WARN: serial-number wider than 32 bits ('$SERIAL_NUM'), using built-in MACs"
                else
                    # 32-bit big-endian base, then offset. The offsets are
                    # applied to the whole value so a carry propagates.
                    _base=$(printf '%d' "0x$SERIAL_NUM")
                    _dev=$(( (_base + 2) & 0xFFFFFFFF ))
                    _host=$(( (_base + 3) & 0xFFFFFFFF ))
                    DEV_MAC=$(printf '02:00:%02x:%02x:%02x:%02x' \
                        $(( (_dev >> 24) & 0xFF )) $(( (_dev >> 16) & 0xFF )) \
                        $(( (_dev >> 8) & 0xFF )) $(( _dev & 0xFF )))
                    HOST_MAC=$(printf '02:00:%02x:%02x:%02x:%02x' \
                        $(( (_host >> 24) & 0xFF )) $(( (_host >> 16) & 0xFF )) \
                        $(( (_host >> 8) & 0xFF )) $(( _host & 0xFF )))
                    log "MAC from serial $SERIAL_NUM: dev=$DEV_MAC host=$HOST_MAC"
                fi
                ;;
        esac
    fi

    # Only reached when neither the override nor the serial worked.
    [ -n "$DEV_MAC" ]  || DEV_MAC=02:00:26:e0:41:be
    [ -n "$HOST_MAC" ] || HOST_MAC=02:00:26:e0:41:bf
}

gadget_down() {
    [ -d "$GADGET" ] || return 0
    echo "" > "$GADGET/UDC" 2>/dev/null || true
    rm -f "$GADGET"/configs/*/rndis.usb0 2>/dev/null || true
    rm -f "$GADGET"/os_desc/c.* 2>/dev/null || true
    rmdir "$GADGET"/configs/*/strings/0x409 2>/dev/null || true
    rmdir "$GADGET"/configs/* 2>/dev/null || true
    rmdir "$GADGET"/functions/rndis.usb0/os_desc/interface.rndis 2>/dev/null || true
    rmdir "$GADGET"/functions/rndis.usb0/os_desc 2>/dev/null || true
    rmdir "$GADGET"/functions/rndis.usb0 2>/dev/null || true
    rmdir "$GADGET"/strings/0x409 2>/dev/null || true
    rmdir "$GADGET"/os_desc 2>/dev/null || true
    rmdir "$GADGET" 2>/dev/null || true
}

gadget_up() {
    gadget_down
    mkdir -p "$GADGET"
    cd "$GADGET"

    # Keep the Qualcomm VID/PID the dongle already enumerates with; the host
    # binds on the OS-descriptor compatible ID, not on this pair.
    echo 0x05c6 > idVendor
    echo 0x90b4 > idProduct
    echo 0x0200 > bcdUSB
    echo 0x0100 > bcdDevice

    # Composite device -> Windows loads usbccgp and hands MI_00 to the
    # function driver instead of trying to drive the whole device.
    echo 0xEF > bDeviceClass
    echo 0x02 > bDeviceSubClass
    echo 0x01 > bDeviceProtocol

    mkdir -p strings/0x409
    echo "410stick" > strings/0x409/manufacturer
    echo "UFI003-02 LTE dongle" > strings/0x409/product
    # Per-unit, so two sticks on one host are two distinct USB devices rather
    # than the same one re-plugged. Hosts key their device instance on this.
    echo "ufi003-${SERIAL_NUM:-unknown}" > strings/0x409/serialnumber

    mkdir -p configs/c.1/strings/0x409
    echo "RNDIS" > configs/c.1/strings/0x409/configuration
    echo 500 > configs/c.1/MaxPower
    echo 0x80 > configs/c.1/bmAttributes

    mkdir -p functions/rndis.usb0
    # The actual fix: 02/06/00 (ECM) -> E0/01/03 (RNDIS).
    echo 0xE0 > functions/rndis.usb0/class
    echo 0x01 > functions/rndis.usb0/subclass
    echo 0x03 > functions/rndis.usb0/protocol
    # Fixed MACs so the host keeps the same DHCP lease across reboots.
    echo "$DEV_MAC" > functions/rndis.usb0/dev_addr
    echo "$HOST_MAC" > functions/rndis.usb0/host_addr

    # Microsoft OS descriptors -- this is what makes Windows auto-bind.
    mkdir -p functions/rndis.usb0/os_desc/interface.rndis
    echo "RNDIS" > functions/rndis.usb0/os_desc/interface.rndis/compatible_id
    echo "5162001" > functions/rndis.usb0/os_desc/interface.rndis/sub_compatible_id

    mkdir -p os_desc
    echo 1 > os_desc/use
    echo 0xcd > os_desc/b_vendor_code
    echo "MSFT100" > os_desc/qw_sign

    ln -s functions/rndis.usb0 configs/c.1/
    ln -s configs/c.1 os_desc/

    echo "$UDC_NAME" > UDC
    log "gadget bound to $UDC_NAME (RNDIS E0/01/03 + MSFT os_desc)"
}

net_up() {
    i=0
    while [ ! -e /sys/class/net/usb0 ] && [ "$i" -lt 100 ]; do
        sleep 0.1
        i=$((i + 1))
    done
    if [ ! -e /sys/class/net/usb0 ]; then
        log "ERROR: usb0 never appeared"
        return 1
    fi

    # Keep NetworkManager from fighting us over the address (runtime + persistent).
    mkdir -p /etc/NetworkManager/conf.d
    printf '[keyfile]\nunmanaged-devices=interface-name:usb0\n' \
        > /etc/NetworkManager/conf.d/99-usb-lan.conf
    nmcli dev set usb0 managed no 2>/dev/null || true

    ip link set usb0 up
    ip addr flush dev usb0
    ip addr add "$LAN_IP/$LAN_PREFIX" dev usb0
    ip addr add "$LEGACY_IP/16" dev usb0
    echo 1 > /proc/sys/net/ipv4/ip_forward
    log "usb0 = $LAN_IP/$LAN_PREFIX (+ $LEGACY_IP/16 fallback)"
}

dhcp_up() {
    mkdir -p /etc/usb-lan
    cat > "$DNSMASQ_CONF" <<EOF
# Served by usb-lan.sh -- DHCP only, DNS is pushed straight to the clients.
interface=usb0
bind-interfaces
port=0
dhcp-range=192.168.100.10,192.168.100.100,255.255.255.0,12h
dhcp-option=1,255.255.255.0
dhcp-option=3,192.168.100.1
dhcp-option=6,223.5.5.5,114.114.114.114
no-resolv
no-hosts
log-dhcp
EOF

    # Stop a previous instance, but only if the pid in the file really is our
    # dnsmasq. A stale pidfile can point at a recycled pid, and killing that
    # would take out an unrelated daemon.
    if [ -f "$PIDFILE" ]; then
        _old=$(cat "$PIDFILE" 2>/dev/null || true)
        if [ -n "$_old" ] && [ -r "/proc/$_old/cmdline" ] && \
           tr '\0' ' ' < "/proc/$_old/cmdline" | grep -q "$DNSMASQ_CONF"; then
            kill "$_old" 2>/dev/null || true
            sleep 0.3
        fi
        rm -f "$PIDFILE"
    fi
    dnsmasq --conf-file="$DNSMASQ_CONF" --pid-file="$PIDFILE"
    log "dnsmasq DHCP up on usb0 (192.168.100.10-100)"
}

nat_up() {
    command -v nft >/dev/null 2>&1 || return 0
    nft list table ip nat >/dev/null 2>&1 || nft add table ip nat
    if ! nft list chain ip nat postrouting >/dev/null 2>&1; then
        nft add chain ip nat postrouting \
            '{ type nat hook postrouting priority srcnat; policy accept; }'
    fi
    if ! nft list chain ip nat postrouting | grep -q '192\.168\.100\.0/24'; then
        nft add rule ip nat postrouting \
            oifname "wwan*" ip saddr 192.168.100.0/24 masquerade
    fi
    log "NAT: 192.168.100.0/24 -> wwan* masquerade"
}

do_up() {
    resolve_macs
    gadget_up
    net_up
    dhcp_up
    nat_up
}

do_down() {
    if [ -f "$PIDFILE" ]; then
        _old=$(cat "$PIDFILE" 2>/dev/null || true)
        if [ -n "$_old" ] && [ -r "/proc/$_old/cmdline" ] && \
           tr '\0' ' ' < "/proc/$_old/cmdline" | grep -q "$DNSMASQ_CONF"; then
            kill "$_old" 2>/dev/null || true
        fi
        rm -f "$PIDFILE"
    fi
    gadget_down
    log "down"
}

do_status() {
    echo "--- gadget ---"
    [ -d "$GADGET" ] && {
        echo "UDC      : $(cat "$GADGET/UDC" 2>/dev/null)"
        echo "idVendor : $(cat "$GADGET/idVendor" 2>/dev/null)"
        echo "idProduct: $(cat "$GADGET/idProduct" 2>/dev/null)"
        echo "class    : $(cat "$GADGET/functions/rndis.usb0/class" 2>/dev/null)"
        echo "subclass : $(cat "$GADGET/functions/rndis.usb0/subclass" 2>/dev/null)"
        echo "protocol : $(cat "$GADGET/functions/rndis.usb0/protocol" 2>/dev/null)"
        echo "os_desc  : use=$(cat "$GADGET/os_desc/use" 2>/dev/null) vendor=$(cat "$GADGET/os_desc/b_vendor_code" 2>/dev/null) sign=$(cat "$GADGET/os_desc/qw_sign" 2>/dev/null)"
        echo "compat_id: $(cat "$GADGET/functions/rndis.usb0/os_desc/interface.rndis/compatible_id" 2>/dev/null)"
        echo "subcomp  : $(cat "$GADGET/functions/rndis.usb0/os_desc/interface.rndis/sub_compatible_id" 2>/dev/null)"
        # Read the live values, not what resolve_macs would compute now.
        echo "dev_addr : $(cat "$GADGET/functions/rndis.usb0/dev_addr" 2>/dev/null)"
        echo "host_addr: $(cat "$GADGET/functions/rndis.usb0/host_addr" 2>/dev/null)"
    }
    echo "--- identity ---"
    echo "serial   : $(tr -d '\000 \n\t' < /sys/firmware/devicetree/base/serial-number 2>/dev/null || echo n/a)"
    [ -f "$MAC_CONF" ] && echo "override : $MAC_CONF" || echo "override : none (derived from serial)"
    echo "--- net ---"
    ip -br addr show usb0 2>/dev/null || echo "usb0 missing"
    echo "--- dhcp ---"
    # Do not use kill -0 here: dnsmasq drops privileges to the dnsmasq user,
    # so an unprivileged status run gets EPERM and reports a healthy server as
    # dead. /proc/<pid> is readable regardless of ownership.
    if [ -f "$PIDFILE" ] && [ -d "/proc/$(cat "$PIDFILE" 2>/dev/null)" ]; then
        echo "dnsmasq pid $(cat "$PIDFILE") running"
    else
        echo "dnsmasq not running"
    fi
}

case "${1:-up}" in
    up)     do_up ;;
    down)   do_down ;;
    status) do_status ;;
    # Print what this unit would use, without touching the gadget. Handy when
    # checking several sticks against the same inventory sheet.
    mac)    resolve_macs
            echo "serial   : ${SERIAL_NUM:-n/a}"
            echo "dev_addr : $DEV_MAC"
            echo "host_addr: $HOST_MAC" ;;
    *)      echo "usage: $0 {up|down|status|mac}" >&2; exit 2 ;;
esac
