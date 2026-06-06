#!/usr/bin/env python3
"""Inspect and split Qualcomm eMMC whole-disk images with a primary GPT."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path


SECTOR_SIZE = 512
UNSAFE_BY_DEFAULT = {
    "modemst1",
    "modemst2",
    "fsg",
    "fsc",
    "ssd",
    "persist",
    "userdata",
    "cache",
}


@dataclass(frozen=True)
class Partition:
    index: int
    name: str
    first_lba: int
    last_lba: int

    @property
    def offset(self) -> int:
        return self.first_lba * SECTOR_SIZE

    @property
    def size(self) -> int:
        return (self.last_lba - self.first_lba + 1) * SECTOR_SIZE

    @property
    def safe_default(self) -> bool:
        return self.name not in UNSAFE_BY_DEFAULT


def decode_gpt_name(raw: bytes) -> str:
    return raw.decode("utf-16le", errors="ignore").rstrip("\0")


def parse_gpt(image: Path) -> list[Partition]:
    with image.open("rb") as fh:
        fh.seek(SECTOR_SIZE)
        header = fh.read(SECTOR_SIZE)
        if header[:8] != b"EFI PART":
            raise ValueError(f"primary GPT header not found in {image}")

        entries_lba = struct.unpack_from("<Q", header, 72)[0]
        entry_count = struct.unpack_from("<I", header, 80)[0]
        entry_size = struct.unpack_from("<I", header, 84)[0]
        if entry_size < 128:
            raise ValueError(f"unsupported GPT entry size: {entry_size}")

        fh.seek(entries_lba * SECTOR_SIZE)
        entries = fh.read(entry_count * entry_size)

    partitions: list[Partition] = []
    for i in range(entry_count):
        entry = entries[i * entry_size : (i + 1) * entry_size]
        if len(entry) < entry_size or entry[:16] == b"\0" * 16:
            continue
        first_lba = struct.unpack_from("<Q", entry, 32)[0]
        last_lba = struct.unpack_from("<Q", entry, 40)[0]
        name = decode_gpt_name(entry[56:128])
        partitions.append(Partition(i + 1, name, first_lba, last_lba))
    return partitions


def partition_dict(partition: Partition) -> dict[str, object]:
    data = asdict(partition)
    data["offset"] = partition.offset
    data["size"] = partition.size
    data["safe_default"] = partition.safe_default
    return data


def selected_partitions(
    partitions: list[Partition],
    names: list[str] | None,
    include_unsafe: bool,
) -> list[Partition]:
    wanted = set(names or [p.name for p in partitions])
    return [p for p in partitions if p.name in wanted and (include_unsafe or p.safe_default)]


def extract_partitions(
    image: Path,
    output_dir: Path,
    names: list[str] | None = None,
    include_unsafe: bool = False,
) -> list[Partition]:
    partitions = selected_partitions(parse_gpt(image), names, include_unsafe)
    output_dir.mkdir(parents=True, exist_ok=True)
    with image.open("rb") as src:
        for partition in partitions:
            src.seek(partition.offset)
            out_path = output_dir / f"{partition.name}.img"
            with out_path.open("wb") as dst:
                copy_exact(src, dst, partition.size)
    return partitions


def copy_exact(src, dst, size: int, chunk_size: int = 1024 * 1024) -> None:
    remaining = size
    while remaining:
        chunk = src.read(min(chunk_size, remaining))
        if not chunk:
            raise EOFError(f"unexpected end of input with {remaining} byte(s) left")
        dst.write(chunk)
        remaining -= len(chunk)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_markdown(image: Path, partitions: list[Partition]) -> str:
    lines = [
        f"# GPT 摘要：{image.name}",
        "",
        f"- 文件大小：`{image.stat().st_size}` bytes",
        f"- SHA-256：`{sha256_file(image)}`",
        "",
        "| # | 分区 | Offset | Size | 默认可切出 |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for p in partitions:
        safe = "yes" if p.safe_default else "no"
        lines.append(f"| {p.index} | `{p.name}` | {p.offset} | {p.size} | {safe} |")
    lines.append("")
    lines.append("`默认可切出 = no` 表示含个体校准/持久化/大数据分区，工具默认不导出，避免误当作可刷写候选。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Whole-disk image with a primary GPT")
    parser.add_argument("--output-dir", type=Path, help="Directory for extracted partitions")
    parser.add_argument("--partitions", nargs="*", help="Partition names to extract or report")
    parser.add_argument("--include-unsafe", action="store_true", help="Allow calibration/persistent partitions")
    parser.add_argument("--json", type=Path, help="Write GPT summary JSON")
    parser.add_argument("--markdown", type=Path, help="Write GPT summary Markdown")
    args = parser.parse_args()

    if not args.image.is_file():
        parser.error(f"image does not exist: {args.image}")

    partitions = parse_gpt(args.image)
    if args.output_dir:
        extracted = extract_partitions(args.image, args.output_dir, args.partitions, args.include_unsafe)
        print(f"extracted {len(extracted)} partition(s) to {args.output_dir}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps([partition_dict(p) for p in partitions], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    markdown = render_markdown(args.image, partitions)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown, encoding="utf-8")
    elif not args.json and not args.output_dir:
        print(markdown, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
