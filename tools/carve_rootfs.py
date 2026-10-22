#!/usr/bin/env python3
"""Carve the root filesystem out of a pmbootstrap disk image.

`pmbootstrap install` without --split produces a *disk* image: a GPT with a
pmos_boot partition and a pmos_root partition.  That image is meant to be
written to a whole device, not to a partition.  edl.exe /w /puserdata writes
into a partition, so feeding it the disk image nests a partition table inside
userdata and the kernel finds no root filesystem.

This tool extracts the root partition so the result is a plain ext4 image that
can be written to userdata directly.

Usage
    carve_rootfs.py <disk.img> [-o <out.img>] [-p NAME|INDEX] [-n]

    -o   output path (default: <input stem>-rootfs.img)
    -p   partition by GPT name or 1-based index (default: auto)
    -n   dry run, only report what would be extracted

Input may be an Android sparse image; it is converted to a temporary raw file
first because carving needs random access.

Default partition selection: the largest partition whose name looks like a
root filesystem, else simply the largest partition.  pmbootstrap names them
pmos_boot / pmos_root, so the size heuristic is only a fallback.

Exit codes
    0  extracted (or dry run reported)
    1  error
    2  the input is already a plain ext4 image, nothing to do
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sparse2raw import SPARSE_HEADER_MAGIC, convert as sparse_to_raw  # noqa: E402

SECTOR = 512
GPT_SIG = b"EFI PART"
EXT4_MAGIC_OFFSET = 1080
EXT4_MAGIC = b"\x53\xef"

# Partition type GUIDs that we are willing to call "the root filesystem".
# Linux filesystem data is what pmbootstrap uses.
LINUX_FS_TYPES = {
    "0fc63daf-8483-4772-8e79-3d69d8477de4",
    "44479540-f297-41b2-9af7-d131d5f0458a",  # root x86
    "4f68bce3-e8cd-4db1-96e7-fbcaf984b709",  # root x86-64
    "69dad710-2ce4-4e3c-b16c-21a1d49abed3",  # root arm64
}


def is_sparse(path: Path) -> bool:
    with open(path, "rb") as f:
        head = f.read(4)
    return len(head) == 4 and struct.unpack("<I", head)[0] == SPARSE_HEADER_MAGIC


def is_ext4_at(f, offset: int) -> bool:
    f.seek(offset + EXT4_MAGIC_OFFSET)
    return f.read(2) == EXT4_MAGIC


def read_gpt(f) -> list[dict]:
    """Return the non-empty GPT entries, or [] if there is no GPT."""
    f.seek(SECTOR)
    header = f.read(92)
    if header[:8] != GPT_SIG:
        return []

    hsz, = struct.unpack_from("<I", header, 12)
    if hsz < 92:
        raise ValueError(f"implausible GPT header size {hsz}")

    entry_lba, = struct.unpack_from("<Q", header, 72)
    nent, esz = struct.unpack_from("<II", header, 80)
    if not (0 < nent <= 1024 and 128 <= esz <= 4096):
        raise ValueError(f"implausible GPT entry array {nent} x {esz}")

    f.seek(entry_lba * SECTOR)
    raw = f.read(nent * esz)
    if len(raw) != nent * esz:
        raise ValueError("truncated GPT entry array")

    out = []
    for i in range(nent):
        e = raw[i * esz:(i + 1) * esz]
        if e[:16] == b"\x00" * 16:
            continue
        first, last, attr = struct.unpack_from("<QQQ", e, 32)
        name = e[56:128].decode("utf-16-le", "replace").split("\x00")[0]
        out.append({
            "index": i + 1,
            "type": str(uuid.UUID(bytes_le=e[:16])),
            "unique": str(uuid.UUID(bytes_le=e[16:32])),
            "first": first,
            "last": last,
            "attr": attr,
            "name": name,
        })
    return out


def pick(parts: list[dict], spec: str | None) -> dict:
    if spec:
        if spec.isdigit():
            idx = int(spec)
            for p in parts:
                if p["index"] == idx:
                    return p
            raise SystemExit(f"no partition with index {idx}")
        for p in parts:
            if p["name"] == spec:
                return p
        names = ", ".join(f'{p["index"]}:{p["name"]}' for p in parts)
        raise SystemExit(f"no partition named {spec!r} (have {names})")

    named = [p for p in parts if "root" in p["name"].lower()]
    pool = named or [p for p in parts if p["type"] in LINUX_FS_TYPES] or parts
    return max(pool, key=lambda p: p["last"] - p["first"])


def human(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n} B"


def carve(src: Path, dst: Path, spec: str | None, dry: bool) -> int:
    tmp_raw: Path | None = None
    work = src

    try:
        if is_sparse(src):
            print(f"input is sparse, converting to a temporary raw file first")
            fd, tmp_name = tempfile.mkstemp(prefix="carve_", suffix=".raw")
            os.close(fd)
            tmp_raw = Path(tmp_name)
            sparse_to_raw(str(src), str(tmp_raw))
            work = tmp_raw

        size = work.stat().st_size
        with open(work, "rb") as f:
            # Already a bare filesystem? Then there is nothing to carve.
            if is_ext4_at(f, 0):
                print(f"{src} is already a plain ext4 image - nothing to carve")
                return 2

            parts = read_gpt(f)
            if not parts:
                raise SystemExit(
                    f"{src}: no GPT found and not ext4 - cannot tell what this is")

            print(f"disk image : {src}  ({human(size)})")
            print(f"partitions : {len(parts)}")
            for p in parts:
                nbytes = (p["last"] - p["first"] + 1) * SECTOR
                print(f'  [{p["index"]}] {p["name"] or "(unnamed)":<12} '
                      f'LBA {p["first"]:>10,} .. {p["last"]:>10,}  {human(nbytes)}')

            target = pick(parts, spec)
            first, last = target["first"], target["last"]
            nbytes = (last - first + 1) * SECTOR
            offset = first * SECTOR
            if offset + nbytes > size:
                raise SystemExit(
                    f"partition extends past end of image "
                    f"({offset + nbytes:,} > {size:,})")

            print()
            print(f'selected   : [{target["index"]}] {target["name"] or "(unnamed)"}')
            print(f"offset     : {offset:,} B  (LBA {first:,})")
            print(f"size       : {human(nbytes)}")

            if dry:
                print("\ndry run - nothing written")
                return 0

            if not is_ext4_at(f, offset):
                f.seek(offset)
                head = f.read(4)
                raise SystemExit(
                    f"selected partition is not ext4 (first bytes {head.hex()}); "
                    f"refusing to write it as a root filesystem")

            f.seek(offset)
            written = 0
            with open(dst, "wb") as w:
                while written < nbytes:
                    chunk = f.read(min(4 << 20, nbytes - written))
                    if not chunk:
                        raise SystemExit("short read while copying partition")
                    w.write(chunk)
                    written += len(chunk)

        print(f"\nwrote {dst}  ({human(dst.stat().st_size)})")

        with open(dst, "rb") as v:
            if not is_ext4_at(v, 0):
                raise SystemExit("output failed ext4 verification")
        print("verified: output is a plain ext4 filesystem")
        return 0

    finally:
        if tmp_raw is not None:
            try:
                tmp_raw.unlink()
            except OSError:
                pass


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Carve the root filesystem out of a pmbootstrap disk image")
    ap.add_argument("image", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("-p", "--partition",
                    help="GPT partition name or 1-based index")
    ap.add_argument("-n", "--dry-run", action="store_true")
    args = ap.parse_args(argv[1:])

    src = args.image
    if not src.is_file():
        raise SystemExit(f"no such file: {src}")

    dst = args.output or src.with_name(src.stem + "-rootfs.img")
    if dst.exists() and not args.dry_run:
        print(f"overwriting {dst}")

    return carve(src, dst, args.partition, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
