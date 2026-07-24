#!/usr/bin/env bash
set -eu

: "${OUTPUT:=/build/out}"
: "${JOBS:=$(nproc)}"
: "${REPO:=}"
: "${PMBOOTSTRAP_WORK:=/build/pmbootstrap}"
: "${CFG:=/repo/config/pmbootstrap-build.cfg}"
: "${PMAPORTS_DIR:=/build/pmaports}"
: "${DEVICE_OVERLAY:=/repo/config/device-testing}"
: "${DEVICE:=zhihe-ufi003-mb-v02}"

echo "=== Building pmOS rootfs ==="
echo "OUTPUT=$OUTPUT  WORK=$PMBOOTSTRAP_WORK  DEVICE=$DEVICE"

export HOME=/root

# ── 1. Clone official GitLab pmaports ──────────────────────────────
echo "Cloning official pmaports from GitLab..."
git clone --depth=1 --branch=master \
    https://gitlab.postmarketos.org/postmarketOS/pmaports.git "$PMAPORTS_DIR"

# ── 2. Merge local device overlay into pmaports ────────────────────
if [ -d "$DEVICE_OVERLAY" ]; then
    echo "=== Merging device overlay from $DEVICE_OVERLAY ==="
    for device_dir in "$DEVICE_OVERLAY"/*/; do
        [ -d "$device_dir" ] || continue
        devname=$(basename "$device_dir")
        echo "  Adding device: $devname"
        mkdir -p "$PMAPORTS_DIR/device/testing"
        cp -r "$device_dir" "$PMAPORTS_DIR/device/testing/$devname"
    done
fi

# Verify our device was added
DEVICE_DIR="device-${DEVICE}"
if [ ! -f "$PMAPORTS_DIR/device/testing/${DEVICE_DIR}/deviceinfo" ]; then
    echo "ERROR: Device overlay not found for $DEVICE_DIR in $PMAPORTS_DIR/device/testing/"
    exit 1
fi

# pmbootstrap needs the origin/main ref for channels.cfg
git -C "$PMAPORTS_DIR" update-ref refs/remotes/origin/main \
    "$(git -C "$PMAPORTS_DIR" rev-parse HEAD)"

# ── 3. Link config ─────────────────────────────────────────────────
mkdir -p ~/.config
if [ -f "$CFG" ]; then
    cp "$CFG" ~/.config/pmbootstrap.cfg
    echo "Copied config from $CFG"
fi

# ── 4. Init with merged aports (non-interactive via -y) ────────────
pmbootstrap -y --work="$PMBOOTSTRAP_WORK" --aports="$PMAPORTS_DIR" init

# ── 5. Install rootfs ──────────────────────────────────────────────
pmbootstrap -y --work="$PMBOOTSTRAP_WORK" install --no-fde --zap

# ── 6. Collect outputs ─────────────────────────────────────────────
mkdir -p "$OUTPUT"

BOOT_IMG="$PMBOOTSTRAP_WORK/chroot_native/home/pmos/rootfs/${DEVICE}-boot.img"
ROOTFS_IMG="$PMBOOTSTRAP_WORK/chroot_native/home/pmos/rootfs/${DEVICE}.img"

[ -f "$BOOT_IMG" ] && cp "$BOOT_IMG" "$OUTPUT/boot.img" && echo "boot.img: $(ls -lh $OUTPUT/boot.img)"
[ -f "$ROOTFS_IMG" ] && cp "$ROOTFS_IMG" "$OUTPUT/rootfs.img" && echo "rootfs.img: $(ls -lh $OUTPUT/rootfs.img)"

# Fallback: search work dir
if [ ! -f "$OUTPUT/boot.img" ]; then
    echo "Searching work dir for images..."
    find "$PMBOOTSTRAP_WORK" -type f \( -name "*.img" -o -name "boot.img" \) \
        -not -path "*/cache*" 2>/dev/null | head -10
    for f in $(find "$PMBOOTSTRAP_WORK" -type f \( -name "*.img" -o -name "boot.img" \) \
        -not -path "*/cache*" 2>/dev/null); do
        cp "$f" "$OUTPUT/" 2>/dev/null || true
    done
fi

echo "=== Rootfs build complete ==="
ls -lh "$OUTPUT/"
