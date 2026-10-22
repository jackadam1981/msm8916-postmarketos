#!/usr/bin/env python3
"""Assert that a freshly compiled DTB really describes the UFI003_MB_V02.

`dtc` proves that the source parses.  It does not prove that the result is the
board we meant to describe: a `/delete-property/` that silently matched
nothing, an override that landed on the wrong node, or a GPIO number typo all
compile without complaint.

This script re-reads the compiled binary and checks the values that are
actually load-bearing on this device.  Every check below maps to something
observable at boot time, so a failure here is a real bug, not style.

Values are read as raw bytes rather than through dtb_dump.render(), because
render() guesses strings vs cells and gets it wrong for short cell arrays
that happen to look printable (the restart key's <&tlmm 37 GPIO_ACTIVE_HIGH>
renders as a string, for example).

Usage:
    verify_dtb.py <file.dtb> [--expect-mib 512]

Exit code 0 on success, 1 on the first failed check.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dtb_dump import Node, parse  # noqa: E402

MODEL = "UFI003_MB_V02 4G Modem Stick"
COMPATIBLE = ["zhihe,ufi003-mb-v02", "qcom,msm8916"]

# Node suffixes.  Matched as suffixes so a kernel rebase that renames soc@0 to
# soc, or moves a unit address, does not turn into a false alarm.
USB = "usb@78d9000"
USB_PHY = "ulpi/phy"
VENUS = "video-codec@1d00000"
MPSS = "remoteproc@4080000"
MEMORY = "memory@80000000"
BUTTON = "button-restart"
SIM_STATE = "sim-ctrl-default-state"

# name -> (GPIO number, label in the upstream tree).  The three LEDs are wired
# as WIFI_S / 4G_L2 / 4G_S; the ufi001c names are kept because userspace
# scripts already reference them.
LEDS = {
    "led-b": 20,
    "led-g": 21,
    "led-r": 22,
}

# pinconf group -> (pin numbers, level).  SIM_SEL on GPIO 2 is driven HIGH on
# purpose; copying the vendor tree's output-low here breaks card detection.
SIM_PINCONF = {
    "esim-sel-pins": ([0, 3], "output-low"),
    "sim-en-pins": ([1], "output-low"),
    "sim-sel-pins": ([2], "output-high"),
}


class Failure(Exception):
    pass


def find(root: Node, suffix: str) -> Node:
    hits = [n for n in root.walk() if n.path.endswith(suffix)]
    if not hits:
        raise Failure(f"no node ending in {suffix!r} in the compiled tree")
    if len(hits) > 1:
        raise Failure(f"{suffix!r} is ambiguous: {[n.path for n in hits]}")
    return hits[0]


def cells(node: Node, prop: str) -> tuple[int, ...]:
    raw = node.props.get(prop)
    if raw is None:
        raise Failure(f"{node.path}: property {prop!r} is missing")
    if len(raw) % 4:
        raise Failure(f"{node.path}: {prop!r} is {len(raw)} bytes, not a cell array")
    return struct.unpack(f">{len(raw) // 4}I", raw)


def strings(node: Node, prop: str) -> list[str]:
    raw = node.props.get(prop)
    if raw is None:
        raise Failure(f"{node.path}: property {prop!r} is missing")
    if not raw.endswith(b"\x00"):
        raise Failure(f"{node.path}: {prop!r} is not NUL terminated")
    return raw[:-1].decode("utf-8").split("\x00")


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise Failure(msg)


def by_phandle(root: Node, value: int) -> Node:
    for node in root.walk():
        raw = node.props.get("phandle")
        if raw and len(raw) == 4 and struct.unpack(">I", raw)[0] == value:
            return node
    raise Failure(f"no node has phandle {value:#x}")


def check(root: Node, expect_mib: int | None) -> int:
    n = 0

    # ---- board identity -------------------------------------------------
    expect(strings(root, "model") == [MODEL],
           f"model is {strings(root, 'model')!r}, expected {[MODEL]!r}")
    expect(strings(root, "compatible") == COMPATIBLE,
           f"compatible is {strings(root, 'compatible')!r}, expected {COMPATIBLE!r}")
    expect(strings(root, "chassis-type") == ["embedded"],
           f"chassis-type is {root.props.get('chassis-type')!r}, expected 'embedded'")
    n += 3

    # ---- memory ---------------------------------------------------------
    # Pinned instead of left at 0 for the bootloader to fill in, because the
    # hand-built DTB this board shipped with hardcoded 512 MiB and that is the
    # configuration known to boot.
    mem = find(root, MEMORY)
    reg = cells(mem, "reg")
    expect(len(reg) == 4, f"{mem.path}: reg has {len(reg)} cells, expected 4")
    expect(reg[1] == 0x80000000, f"{mem.path}: base is {reg[1]:#x}, expected 0x80000000")
    if expect_mib is not None:
        want = expect_mib * 1024 * 1024
        expect(reg[3] == want, f"{mem.path}: size is {reg[3]:#x}, expected {want:#x}")
    n += 1

    # ---- USB: peripheral only -------------------------------------------
    # This is a dongle.  Host mode has no gadget registered and no console, so
    # a role switch here is a way to make the device disappear.
    usb = find(root, USB)
    expect(strings(usb, "dr_mode") == ["peripheral"],
           f"{usb.path}: dr_mode is {usb.props.get('dr_mode')!r}, expected 'peripheral'")
    expect("usb-role-switch" not in usb.props,
           f"{usb.path}: usb-role-switch should have been deleted but is present")
    n += 2

    # extcon is the old cable-detection binding; the dts deletes it from both
    # the controller and the PHY.  Nothing on this board should still have it.
    stale = [node.path for node in root.walk() if "extcon" in node.props]
    expect(not stale, f"extcon is still present on: {stale}")
    n += 1

    # The PHY rails come from the PMIC, not from board-level fixed
    # regulators.  The vendor tree says the same: HSUSB_1p8-supply points at
    # 8916_l7 and HSUSB_3p3-supply at 8916_l13.  The old hand-built DTB used
    # regulator-fixed stubs here, which is a leftover from an older kernel and
    # hides whether the rails are actually controlled.
    phy = find(root, USB_PHY)
    for prop, rail in (("v1p8-supply", "l7"), ("v3p3-supply", "l13")):
        cells_ = cells(phy, prop)
        target = by_phandle(root, cells_[0])
        expect(target.path.endswith("regulators/" + rail),
               f"{phy.path}: {prop} points at {target.path}, expected the "
               f"PMIC {rail.upper()} rail (regulators/{rail})")
        n += 1

    # ---- venus off ------------------------------------------------------
    venus = find(root, VENUS)
    expect(strings(venus, "status") == ["disabled"],
           f"{venus.path}: status is {venus.props.get('status')!r}, expected 'disabled'")
    n += 1

    # ---- modem up, with the SIM mux attached ----------------------------
    mpss = find(root, MPSS)
    expect(strings(mpss, "status") == ["okay"],
           f"{mpss.path}: status is {mpss.props.get('status')!r}, expected 'okay'")
    expect("pinctrl-0" in mpss.props,
           f"{mpss.path}: pinctrl-0 missing - the SIM mux would stay unconfigured")
    n += 2

    # ---- GPIO wiring ----------------------------------------------------
    for name, gpio in LEDS.items():
        led = find(root, name)
        g = cells(led, "gpios")
        expect(len(g) >= 2, f"{led.path}: gpios has {len(g)} cell(s)")
        expect(g[1] == gpio, f"{led.path}: wired to GPIO {g[1]}, expected {gpio}")
        n += 1

    btn = find(root, BUTTON)
    g = cells(btn, "gpios")
    expect(len(g) >= 2, f"{btn.path}: gpios has {len(g)} cell(s)")
    expect(g[1] == 37, f"{btn.path}: wired to GPIO {g[1]}, expected 37")
    n += 1

    # ---- SIM mux pinconf ------------------------------------------------
    # Both the pin list and the driven level matter: the vendor tree parks
    # SIM_SEL low and uses a different route through ESIM_SEL, and copying
    # that makes the card undetectable here.
    #
    # Look the groups up as children of the pinctrl state by exact name.
    # Suffix matching does not work here: "sim-sel-pins" is a suffix of
    # "esim-sel-pins", so a naive match reports every group as ambiguous.
    sim = find(root, SIM_STATE)
    for group, (pins, level) in SIM_PINCONF.items():
        matches = [c for c in sim.children if c.name == group]
        expect(len(matches) == 1,
               f"{sim.path}: expected one child named {group!r}, found {len(matches)}")
        node = matches[0]
        got = strings(node, "pins")
        nums = [int(p.removeprefix("gpio")) for p in got]
        expect(nums == pins, f"{node.path}: pins are {nums}, expected {pins}")
        expect(level in node.props,
               f"{node.path}: {level!r} is missing (has {sorted(node.props)})")
        n += 1

    return n


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: verify_dtb.py <file.dtb> [--expect-mib 512]")
        return 2

    path = argv[1]
    expect_mib = 512
    if "--expect-mib" in argv:
        expect_mib = int(argv[argv.index("--expect-mib") + 1])

    root, hdr = parse(path)
    nodes = sum(1 for _ in root.walk())
    print(f"# {path}: {hdr['totalsize']} bytes, {nodes} nodes")

    try:
        n = check(root, expect_mib)
    except Failure as exc:
        print(f"FAIL: {exc}")
        return 1

    print(f"OK: {n} board-specific assertions passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
