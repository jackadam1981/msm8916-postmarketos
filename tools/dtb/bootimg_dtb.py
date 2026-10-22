#!/usr/bin/env python3
"""Extract the device tree that pmOS appends to the kernel inside boot.img.

pmbootstrap builds an Android boot image for msm8916.  The board DTB is not in
the `second` area - deviceinfo_append_dtb makes the kernel build glue it onto
the end of the kernel blob, so kernel_size covers Image + dtb.  That is why
`unpackbootimg` shows a kernel that is ~50 KiB larger than the vmlinux, and why
looking for the dtb anywhere else finds nothing.

This walks the header, scans the kernel region for an FDT magic, and writes the
blob out so verify_dtb.py can assert on it.  The scan is bounded by kernel_size,
so a stray 0xd00dfeed inside compressed data cannot pull in trailing bytes: the
candidate has to declare a totalsize that fits inside the kernel region.

Usage:
    python tools/dtb/bootimg_dtb.py extract boot.img -o out/
    python tools/dtb/bootimg_dtb.py info boot.img
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

FDT_MAGIC = 0xD00DFEED
BOOT_MAGIC = b"ANDROID!"


def parse_header(data: bytes) -> dict:
    if not data.startswith(BOOT_MAGIC):
        raise SystemExit(
            "not an Android boot image (magic is %r).  On this project the "
            "PMOS whole-disk image also ends in .img - pass the 23 MiB one."
            % data[:8]
        )
    (kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size,
     second_addr, tags_addr, page_size, header_version, os_version) = \
        struct.unpack_from("<10I", data, 8)
    if page_size == 0 or page_size & (page_size - 1):
        raise SystemExit(f"implausible page size {page_size}")
    out = {
        "kernel_size": kernel_size,
        "kernel_addr": kernel_addr,
        "ramdisk_size": ramdisk_size,
        "ramdisk_addr": ramdisk_addr,
        "second_size": second_size,
        "second_addr": second_addr,
        "tags_addr": tags_addr,
        "page_size": page_size,
        "header_version": header_version,
        "os_version": os_version,
        "name": data[48:64].split(b"\0")[0].decode("ascii", "replace"),
        "cmdline": data[64:576].split(b"\0")[0].decode("ascii", "replace"),
        "image_size": len(data),
    }
    return out


def page_align(n: int, page: int) -> int:
    return (n + page - 1) // page * page


def find_dtbs(kernel: bytes) -> list[tuple[int, int]]:
    """Return (offset, totalsize) for every plausible FDT inside `kernel`."""
    found: list[tuple[int, int]] = []
    pos = 0
    magic = struct.pack(">I", FDT_MAGIC)
    while True:
        pos = kernel.find(magic, pos)
        if pos < 0:
            break
        if pos + 40 <= len(kernel):
            (_, totalsize, off_struct, off_strings, off_rsvmap, version,
             last_comp) = struct.unpack_from(">7I", kernel, pos)
            ok = (
                totalsize >= 40 + 16
                and pos + totalsize <= len(kernel)
                and version >= 16
                and last_comp <= 17
                and off_struct < totalsize
                and off_strings < totalsize
                and off_rsvmap < totalsize
                # a real tree has a NUL-terminated block name right after the
                # structure block's FDT_BEGIN_NODE token
                and struct.unpack_from(">I", kernel, pos + off_struct)[0] == 1
            )
            if ok:
                found.append((pos, totalsize))
                pos += totalsize
                continue
        pos += 4
    return found


def cmd_info(args) -> int:
    data = Path(args.image).read_bytes()
    h = parse_header(data)
    page = h["page_size"]
    kstart = page
    kend = kstart + h["kernel_size"]
    print(f"image            {h['image_size']:,} bytes")
    print(f"page size        {page}")
    print(f"header version   {h['header_version']}")
    print(f"name             {h['name']!r}")
    print(f"cmdline          {h['cmdline']!r}")
    print(f"kernel           offset {kstart:,} size {h['kernel_size']:,}")
    print(f"ramdisk          offset {page_align(kend, page):,} size {h['ramdisk_size']:,}")
    print(f"second           size {h['second_size']:,}"
          + ("  (dtb is NOT here)" if h["second_size"] == 0 else ""))
    kernel = data[kstart:kend]
    dtbs = find_dtbs(kernel)
    if not dtbs:
        print("dtb              NOT FOUND in kernel region")
        return 1
    for off, size in dtbs:
        print(f"dtb              kernel+{off:,} size {size:,} "
              f"(ends at kernel+{off + size:,} of {h['kernel_size']:,})")
    tail = h["kernel_size"] - (dtbs[-1][0] + dtbs[-1][1])
    print(f"trailing bytes   {tail}")
    return 0


def cmd_extract(args) -> int:
    data = Path(args.image).read_bytes()
    h = parse_header(data)
    page = h["page_size"]
    kernel = data[page:page + h["kernel_size"]]
    dtbs = find_dtbs(kernel)
    if not dtbs:
        print("error: no dtb found in the kernel region", file=sys.stderr)
        return 1
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, (off, size) in enumerate(dtbs):
        name = args.name if (args.name and len(dtbs) == 1) else f"dtb-{i:02d}.dtb"
        path = outdir / name
        path.write_bytes(kernel[off:off + size])
        print(f"wrote {path}  {size:,} bytes  (kernel+{off:,})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="print header fields and locate the dtb")
    p.add_argument("image")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("extract", help="write the dtb out of the kernel tail")
    p.add_argument("image")
    p.add_argument("-o", "--output", default="out/bootimg")
    p.add_argument("-n", "--name", default=None,
                   help="output filename (default dtb-NN.dtb)")
    p.set_defaults(func=cmd_extract)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
