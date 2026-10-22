#!/usr/bin/env python3
"""Dump a GPT image (as produced by EDL reads or pmaports tooling).

Accepts either a full "both" image (protective MBR + primary header + entries
+ backup entries + backup header) or a bare primary/backup pair, and prints the
partition table in a readable form.

Usage:
    gpt_dump.py <file.bin> [--csv]
"""

from __future__ import annotations

import struct
import sys
import uuid

SECTOR = 512
GPT_SIG = b"EFI PART"


def guid(raw: bytes) -> str:
    # mixed-endian: first three fields are little endian
    return str(uuid.UUID(bytes_le=raw))


def parse_header(buf: bytes, off: int) -> dict | None:
    if buf[off:off + 8] != GPT_SIG:
        return None
    (rev,) = struct.unpack_from("<I", buf, off + 8)
    hsz, = struct.unpack_from("<I", buf, off + 12)
    cur, backup, first_use, last_use = struct.unpack_from("<QQQQ", buf, off + 24)
    ent_lba, = struct.unpack_from("<Q", buf, off + 72)
    nent, esz = struct.unpack_from("<II", buf, off + 80)
    return {
        "revision": f"{rev >> 16}.{rev & 0xffff}",
        "header_size": hsz,
        "current_lba": cur,
        "backup_lba": backup,
        "first_usable": first_use,
        "last_usable": last_use,
        "entry_lba": ent_lba,
        "num_entries": nent,
        "entry_size": esz,
    }


def parse_entries(buf: bytes, off: int, nent: int, esz: int) -> list[dict]:
    out = []
    for i in range(nent):
        o = off + i * esz
        if o + 128 > len(buf):
            break
        tguid = buf[o:o + 16]
        if tguid == b"\x00" * 16:
            continue
        pguid = buf[o + 16:o + 32]
        first, last, attr = struct.unpack_from("<QQQ", buf, o + 32)
        name = buf[o + 56:o + 128].decode("utf-16-le", "replace").split("\x00")[0]
        out.append({
            "idx": i + 1,
            "name": name,
            "type": guid(tguid),
            "uuid": guid(pguid),
            "first": first,
            "last": last,
            "sectors": last - first + 1,
            "bytes": (last - first + 1) * SECTOR,
            "attr": attr,
        })
    return out


def human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    csv = "--csv" in argv
    buf = open(path, "rb").read()

    # primary header is at LBA1
    hdr = parse_header(buf, SECTOR)
    hdr_off = SECTOR
    if hdr is None:
        # maybe the file starts directly with a header
        hdr = parse_header(buf, 0)
        hdr_off = 0
    if hdr is None:
        print(f"{path}: no GPT header found")
        return 1

    ent_off = hdr_off + (hdr["entry_lba"] - hdr["current_lba"]) * SECTOR
    parts = parse_entries(buf, ent_off, hdr["num_entries"], hdr["entry_size"])

    if csv:
        print("idx,name,start_lba,end_lba,sectors,bytes,type,uuid")
        for p in parts:
            print(f"{p['idx']},{p['name']},{p['first']},{p['last']},{p['sectors']},"
                  f"{p['bytes']},{p['type']},{p['uuid']}")
        return 0

    total = (hdr["backup_lba"] + 1) * SECTOR
    print(f"file            : {path}  ({len(buf):,} B)")
    print(f"gpt revision    : {hdr['revision']}")
    print(f"disk size       : {human(total)}  ({hdr['backup_lba'] + 1:,} sectors)")
    print(f"usable range    : LBA {hdr['first_usable']:,} .. {hdr['last_usable']:,}"
          f"  ({human((hdr['last_usable'] - hdr['first_usable'] + 1) * SECTOR)})")
    print(f"entries         : {hdr['num_entries']} x {hdr['entry_size']} B")
    print()

    parts.sort(key=lambda p: p["first"])
    print(f"{'#':>2}  {'name':<20} {'start':>10} {'end':>10} {'size':>10}")
    print("-" * 58)
    prev_end = None
    total_used = 0
    for p in parts:
        gap = ""
        if prev_end is not None and p["first"] > prev_end + 1:
            gap = f"   <- gap {human((p['first'] - prev_end - 1) * SECTOR)}"
        print(f"{p['idx']:>2}  {p['name']:<20} {p['first']:>10,} {p['last']:>10,} "
              f"{human(p['bytes']):>10}{gap}")
        prev_end = p["last"]
        total_used += p["bytes"]
    print("-" * 58)
    print(f"    {'allocated':<20} {'':>10} {'':>10} {human(total_used):>10}")

    # 最大的空闲块
    free = []
    cur = hdr["first_usable"]
    for p in parts:
        if p["first"] > cur:
            free.append((cur, p["first"] - 1))
        cur = max(cur, p["last"] + 1)
    if cur <= hdr["last_usable"]:
        free.append((cur, hdr["last_usable"]))
    if free:
        print()
        print("free space:")
        for s, e in sorted(free, key=lambda x: -(x[1] - x[0])):
            print(f"  LBA {s:,} .. {e:,}   {human((e - s + 1) * SECTOR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
