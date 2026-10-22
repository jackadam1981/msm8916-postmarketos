#!/usr/bin/env python3
"""Sync the pmaports kernel package overlay from upstream.

pmaports ships `linux-postmarketos-qcom-msm8916` with the kernel source tarball,
two configs and one patch.  We need to add our own device tree patch on top of
that.  Rather than hand-editing (and hand-fixing sha512sums) on every kernel
bump, this script pulls the current upstream APKBUILD and re-applies our two
changes mechanically:

  1. append the dts patch to source="
  2. append its sha512 to sha512sums="
  3. set pkgrel to upstream pkgrel + 1 so the local package always wins over
     the binary repository version

Run it after a pmaports kernel upgrade, then commit the result:

    python scripts/pmaports/sync-kernel-apkbuild.py

It is idempotent: running it twice produces the same file.
"""

from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PACKAGE = "linux-postmarketos-qcom-msm8916"
UPSTREAM_BRANCH = "main"
# pmaports moved this package around; testing/ is where it lives as of 6.12.
UPSTREAM_PATH = f"device/testing/{PACKAGE}/APKBUILD"
API = (
    "https://gitlab.postmarketos.org/api/v4/projects/postmarketOS%2Fpmaports"
    f"/repository/files/{UPSTREAM_PATH.replace('/', '%2F')}/raw?ref={UPSTREAM_BRANCH}"
)

OUT_DIR = ROOT / "config/kernel-testing" / PACKAGE
PATCH_FILE = "0002-arm64-dts-qcom-msm8916-add-zhihe-ufi003-mb-v02.patch"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "pmos-ufi003-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def insert_into_block(text: str, var: str, newline: str, indent: str = "\t") -> str:
    """Append `newline` as the last entry of the multi-line `var="` block."""
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f'{var}="'):
            start = i
            break
    if start is None:
        sys.exit(f'{var}=" block not found')

    # Single-line form: var="a b c"
    if lines[start].rstrip("\n").endswith('"') and len(lines[start].strip()) > len(var) + 2:
        body = lines[start].rstrip("\n")
        lines[start] = body[:-1].rstrip() + "\n" + indent + newline + '\n"\n'
        return "".join(lines)

    # Multi-line form: closing quote sits alone on its own line.
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == '"':
            lines.insert(j, f"{indent}{newline}\n")
            return "".join(lines)
    sys.exit(f'{var}=" block is not terminated by a lone quote')


def main() -> int:
    print(f"fetching {API}")
    upstream = fetch(API)
    pkgver = re.search(r"^pkgver=(.+)$", upstream, re.M)
    pkgrel = re.search(r"^pkgrel=(\d+)$", upstream, re.M)
    if not pkgver or not pkgrel:
        sys.exit("could not parse pkgver/pkgrel from upstream APKBUILD")

    apkbuild = upstream

    # 1. register the patch
    apkbuild = insert_into_block(apkbuild, "source", PATCH_FILE)

    # 2. add its checksum
    patch_path = OUT_DIR / PATCH_FILE
    if not patch_path.is_file():
        sys.exit(f"missing patch: {patch_path}")
    digest = hashlib.sha512(patch_path.read_bytes()).hexdigest()
    apkbuild = insert_into_block(apkbuild, "sha512sums", f"{digest}  {PATCH_FILE}", indent="")

    # 3. make sure the local package outranks the binary repo one
    new_rel = int(pkgrel.group(1)) + 1
    apkbuild = re.sub(r"^pkgrel=\d+$", f"pkgrel={new_rel}", apkbuild, count=1, flags=re.M)

    header = (
        "# Overlay of pmaports device/testing/linux-postmarketos-qcom-msm8916\n"
        "# Regenerate with: python scripts/pmaports/sync-kernel-apkbuild.py\n"
        "# Local changes: adds the UFI003_MB_V02 device tree patch, pkgrel + 1.\n"
    )
    apkbuild = header + apkbuild

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "APKBUILD"
    out.write_text(apkbuild, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  upstream pkgver={pkgver.group(1)} pkgrel={pkgrel.group(1)} -> local pkgrel={new_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
