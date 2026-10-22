#!/usr/bin/env python3
"""Build a postmarketOS GPT for the UFI003-02 eMMC.

Starting point is the stock GPT read off the device (backup/UFI003-1/
gpt_main0.bin, 27 partitions).  Everything the bootloader and the modem need
stays exactly where Qualcomm put it; only the Android-only partitions at the
end of the disk are rearranged:

    keep   LBA 131,072 .. 396,383   modem, sbl1, aboot, tz, hyp, misc,
                                    modemst1/2, fsg, splash, DDR, ...
                                    (untouched, same LBA, same GUIDs)

    boot   396,384 .. 461,919   32 MiB   was 16 MiB - boot.img is 22.4 MiB
    persist 461,920 .. 527,455  32 MiB   moved here so userdata is contiguous
    userdata 527,456 .. 7,405,534  3.28 GiB

    dropped: system (800 MiB), cache (128 MiB), recovery (16 MiB)

Moving persist means its contents have to be preserved by the caller: read it
out before writing this table and write it back to the new offset afterwards.
`flash_edl_original.bat` already dumps persist to backup/ before touching
anything, it just needs the extra write-back step.

Usage:
    make_pmos_gpt.py [--src PATH] [--outdir DIR] [--boot-mb N] [--persist-mb N]
"""

from __future__ import annotations

import argparse
import struct
import sys
import uuid
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTOR = 512
GPT_SIG = b"EFI PART"

# Stock layout facts we depend on.
STOCK_LAST_KEEP_LBA = 396_383      # end of "sec", last partition we keep as-is
DISK_LAST_LBA = 7_405_567          # backup header lives here
FIRST_USABLE = 34
LAST_USABLE = 7_405_534


def parse_entries(buf: bytes) -> list[dict]:
    """Read the 128 partition entries starting at LBA 2."""
    out = []
    for i in range(128):
        o = 2 * SECTOR + i * 128
        e = buf[o:o + 128]
        if e[0:16] == b"\x00" * 16:
            continue
        first, last, attr = struct.unpack_from("<QQQ", e, 32)
        out.append({
            "type": e[0:16],
            "unique": e[16:32],
            "first": first,
            "last": last,
            "attr": attr,
            "name": e[56:128].decode("utf-16-le", "replace").split("\x00")[0],
        })
    return out


def build_entry(type_guid: bytes, unique: bytes, first: int, last: int,
                attr: int, name: str) -> bytes:
    e = bytearray(128)
    e[0:16] = type_guid
    e[16:32] = unique
    struct.pack_into("<QQQ", e, 32, first, last, attr)
    n = name.encode("utf-16-le")[:72]
    e[56:56 + len(n)] = n
    return bytes(e)


def build_header(current_lba: int, backup_lba: int, first_usable: int,
                 last_usable: int, disk_guid: bytes, entry_lba: int,
                 array_crc: int) -> bytes:
    h = bytearray(92)
    h[0:8] = GPT_SIG
    struct.pack_into("<I", h, 8, 0x00010000)      # revision 1.0
    struct.pack_into("<I", h, 12, 92)             # header size
    # crc at 16 filled in later
    struct.pack_into("<Q", h, 24, current_lba)
    struct.pack_into("<Q", h, 32, backup_lba)
    struct.pack_into("<Q", h, 40, first_usable)
    struct.pack_into("<Q", h, 48, last_usable)
    h[56:72] = disk_guid
    struct.pack_into("<Q", h, 72, entry_lba)
    struct.pack_into("<I", h, 80, 128)            # num entries
    struct.pack_into("<I", h, 84, 128)            # entry size
    struct.pack_into("<I", h, 88, array_crc)
    struct.pack_into("<I", h, 16, zlib.crc32(bytes(h)) & 0xFFFFFFFF)
    return bytes(h)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "backup/UFI003-1/gpt_main0.bin"))
    ap.add_argument("--outdir", default=str(ROOT / "config/gpt"))
    ap.add_argument("--boot-mb", type=int, default=32)
    ap.add_argument("--persist-mb", type=int, default=32)
    args = ap.parse_args(argv[1:])

    src = Path(args.src)
    if not src.is_file():
        sys.exit(f"stock GPT not found: {src}")
    buf = src.read_bytes()

    stock = parse_entries(buf)
    by_name = {p["name"]: p for p in stock}
    for need in ("boot", "persist", "userdata"):
        if need not in by_name:
            sys.exit(f"stock table has no '{need}' partition")

    disk_guid = buf[SECTOR + 56:SECTOR + 72]

    # 1. everything that starts before the cut line stays untouched
    kept = [p for p in stock if p["first"] < STOCK_LAST_KEEP_LBA]
    kept.sort(key=lambda p: p["first"])

    # 2. new layout after the cut line
    boot_sectors = args.boot_mb * 1024 * 1024 // SECTOR
    persist_sectors = args.persist_mb * 1024 * 1024 // SECTOR

    boot_first = STOCK_LAST_KEEP_LBA + 1
    boot_last = boot_first + boot_sectors - 1
    persist_first = boot_last + 1
    persist_last = persist_first + persist_sectors - 1
    userdata_first = persist_last + 1
    userdata_last = LAST_USABLE

    if userdata_first >= userdata_last:
        sys.exit("not enough room for userdata")

    def reuse(name: str, first: int, last: int) -> dict:
        """Keep the stock GUIDs, move the extent."""
        p = by_name[name]
        return {
            "type": p["type"],
            "unique": p["unique"],
            "first": first,
            "last": last,
            "attr": p["attr"],
            "name": name,
        }

    layout = kept + [
        reuse("boot", boot_first, boot_last),
        reuse("persist", persist_first, persist_last),
        reuse("userdata", userdata_first, userdata_last),
    ]

    # 3. encode the array
    arr = bytearray(128 * 128)
    for i, p in enumerate(layout):
        arr[i * 128:(i + 1) * 128] = build_entry(
            p["type"], p["unique"], p["first"], p["last"], p["attr"], p["name"])
    array_crc = zlib.crc32(bytes(arr)) & 0xFFFFFFFF

    # 4. primary: MBR + header + entries  (34 sectors)
    # The header is 92 bytes but occupies a whole 512-byte sector: without the
    # padding the entry array would land at byte 604 while entry_lba says 2
    # (byte 1024), shifting every field by 420 bytes.
    pad = b"\x00" * (SECTOR - 92)
    mbr = buf[0:SECTOR]
    prim_header = build_header(1, DISK_LAST_LBA, FIRST_USABLE, LAST_USABLE,
                               disk_guid, 2, array_crc)
    primary = mbr + prim_header + pad + bytes(arr)

    # 5. backup: entries at LBA (last-32 .. last-1), header at last
    backup_header = build_header(DISK_LAST_LBA, 1, FIRST_USABLE, LAST_USABLE,
                                 disk_guid, DISK_LAST_LBA - 32, array_crc)
    backup = bytes(arr) + backup_header + pad

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "gpt_pmos_main.bin").write_bytes(primary)
    (outdir / "gpt_pmos_backup.bin").write_bytes(backup)
    (outdir / "gpt_pmos_both.bin").write_bytes(primary + backup)

    print(f"stock   : {src}  ({len(stock)} partitions)")
    print(f"kept    : {len(kept)}  (LBA {kept[0]['first']:,} .. {kept[-1]['last']:,})")
    print(f"dropped : " + ", ".join(p["name"] for p in stock
                                   if p["first"] >= STOCK_LAST_KEEP_LBA))
    print()
    print(f"{'name':<14} {'first':>10} {'last':>10} {'size':>10}")
    print("-" * 48)
    for p in layout:
        n = p["last"] - p["first"] + 1
        print(f"{p['name']:<14} {p['first']:>10,} {p['last']:>10,} "
              f"{n * SECTOR / 1024 / 1024:>9.1f}M")
    print("-" * 48)
    ud = userdata_last - userdata_first + 1
    print(f"userdata was 2.4 GiB, now {ud * SECTOR / 1024 ** 3:.2f} GiB "
          f"(+{(ud - 4_977_535) * SECTOR / 1024 ** 2:.0f} MiB)")
    print()
    print(f"wrote {outdir}/gpt_pmos_main.bin    ({len(primary):,} B)")
    print(f"wrote {outdir}/gpt_pmos_backup.bin  ({len(backup):,} B)")
    print(f"wrote {outdir}/gpt_pmos_both.bin    ({len(primary) + len(backup):,} B)")
    print()
    print("!! persist moved: back it up before flashing and write it back after")
    print(f"   old LBA {by_name['persist']['first']:,} .. {by_name['persist']['last']:,}")
    print(f"   new LBA {persist_first:,} .. {persist_last:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
