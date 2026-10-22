#!/usr/bin/env python3
"""Regenerate the pmaports kernel patch that adds the UFI003 device tree.

The patch is a plain unified diff applied with `patch -p1` by abuild's
default_prepare() inside the kernel source tree, so it must:

  * add arch/arm64/boot/dts/qcom/msm8916-zhihe-ufi003-mb-v02.dts
  * add the matching dtb-$(CONFIG_ARCH_QCOM) line to the dts Makefile

Both are derived from real files instead of being hand-written, so the result
always applies cleanly.  Run this after editing the .dts source:

    python scripts/pmaports/gen-kernel-dts-patch.py

Inputs
    tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts        the board dts source
    tools/dtb/qcom-dts-Makefile.v6.12.1              pristine upstream Makefile
                                                     (refresh when the kernel
                                                     is bumped)

Output
    config/kernel-testing/linux-postmarketos-qcom-msm8916/
        0002-arm64-dts-qcom-msm8916-add-zhihe-ufi003-mb-v02.patch
"""

from __future__ import annotations

import difflib
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DTS_NAME = "msm8916-zhihe-ufi003-mb-v02.dts"
DTS_REL = f"arch/arm64/boot/dts/qcom/{DTS_NAME}"
MAKEFILE_REL = "arch/arm64/boot/dts/qcom/Makefile"
# Insert our dtb right after the UFI001C line so related boards stay together.
ANCHOR = "dtb-$(CONFIG_ARCH_QCOM)\t+= msm8916-thwc-ufi001c.dtb"
NEW_LINE = "dtb-$(CONFIG_ARCH_QCOM)\t+= msm8916-zhihe-ufi003-mb-v02.dtb"

PATCH_NAME = "0002-arm64-dts-qcom-msm8916-add-zhihe-ufi003-mb-v02.patch"
OUT_DIR = ROOT / "config/kernel-testing/linux-postmarketos-qcom-msm8916"

DTS_SRC = ROOT / "tools/dtb" / DTS_NAME
MK_SRC = ROOT / "tools/dtb/qcom-dts-Makefile.v6.12.1"

SUBJECT = "arm64: dts: qcom: msm8916: add Zhihe UFI003_MB_V02"

BODY = """\
Add a device tree for the Zhihe UFI003_MB_V02 4G modem stick (sold as
"410stick", MSM8916 + 512 MiB RAM + 4 GiB eMMC).

The board is electrically identical to the THWC UFI001C: restart key on
GPIO 37, blue/green/red LEDs on GPIO 20/21/22, SIM mux on GPIO 0..3 with the
external slot selected by default.  Only model and compatible differ, so this
file is a near copy of msm8916-thwc-ufi001c.dts.

Three properties are set explicitly because this device is a headless USB
dongle rather than a phone:

  - the memory node is pinned to 512 MiB instead of relying on the bootloader
    to fill it in (this is the configuration that is known to boot here)
  - USB is forced to peripheral mode, role switching is removed
  - venus is left disabled

The DTB used to be shipped as a prebuilt binary in the device package, with
its source lost.  Building it from this file instead makes the board
description reviewable and keeps it in sync with kernel upgrades.
"""


def sha512(path: Path) -> str:
    h = hashlib.sha512()
    h.update(path.read_bytes())
    return h.hexdigest()


def read_lf(path: Path) -> str:
    """Read as text with LF endings.

    The kernel tree is LF, so the diff must be LF too.  A Windows checkout with
    core.autocrlf would otherwise put CR in the context lines and the patch
    would not apply in CI.
    """
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def makefile_hunk() -> str:
    original = read_lf(MK_SRC).splitlines(keepends=True)
    if not any(line.rstrip("\n") == ANCHOR for line in original):
        sys.exit(f"anchor line not found in {MK_SRC}: {ANCHOR!r}")
    patched = []
    for line in original:
        patched.append(line)
        if line.rstrip("\n") == ANCHOR:
            patched.append(NEW_LINE + "\n")
    diff = difflib.unified_diff(
        original,
        patched,
        fromfile="a/" + MAKEFILE_REL,
        tofile="b/" + MAKEFILE_REL,
        n=3,
    )
    return "".join(diff)


def new_file_hunk() -> str:
    text = read_lf(DTS_SRC)
    if not text.endswith("\n"):
        text += "\n"
    lines = text.splitlines(keepends=True)
    out = [
        "--- /dev/null\n",
        f"+++ b/{DTS_REL}\n",
        f"@@ -0,0 +1,{len(lines)} @@\n",
    ]
    out.extend("+" + line for line in lines)
    return "".join(out)


def main() -> int:
    for p in (DTS_SRC, MK_SRC):
        if not p.is_file():
            sys.exit(f"missing input: {p}")

    patch = (
        f"From: postmarketOS MSM8916 port <pmos@localhost>\n"
        f"Subject: [PATCH] {SUBJECT}\n"
        f"\n"
        + "".join(f"{line}\n" if line else "\n" for line in BODY.rstrip("\n").split("\n"))
        + "\n"
        + new_file_hunk()
        + "\n"
        + makefile_hunk()
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / PATCH_NAME
    out.write_text(patch, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)}  ({len(patch)} bytes)")
    print(f"sha512: {sha512(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
