from __future__ import annotations

import importlib.util
import io
import struct
import sys
import tempfile
import unittest
from pathlib import Path


def load_tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "split_qcom_gpt_image.py"
    spec = importlib.util.spec_from_file_location("split_qcom_gpt_image", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_utf16_name(name: str) -> bytes:
    return name.encode("utf-16le").ljust(72, b"\0")


def write_synthetic_gpt(path: Path) -> None:
    data = bytearray(4096)
    data[512:520] = b"EFI PART"
    struct.pack_into("<Q", data, 512 + 72, 2)
    struct.pack_into("<I", data, 512 + 80, 4)
    struct.pack_into("<I", data, 512 + 84, 128)

    def entry(index: int, name: str, first: int, last: int) -> None:
        base = 1024 + index * 128
        data[base : base + 16] = bytes.fromhex("a2a0d0ebe5b9334487c068b6b72699c7")
        data[base + 16 : base + 32] = bytes([index + 1]) * 16
        struct.pack_into("<Q", data, base + 32, first)
        struct.pack_into("<Q", data, base + 40, last)
        data[base + 56 : base + 128] = make_utf16_name(name)

    entry(0, "boot", 4, 5)
    entry(1, "modemst1", 6, 6)
    data[4 * 512 : 6 * 512] = b"B" * 1024
    data[6 * 512 : 7 * 512] = b"M" * 512
    path.write_bytes(data)


class SplitQcomGptImageTests(unittest.TestCase):
    def test_parse_gpt_returns_partition_offsets(self) -> None:
        tool = load_tool()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "disk.bin"
            write_synthetic_gpt(image)

            partitions = tool.parse_gpt(image)

        self.assertEqual([p.name for p in partitions], ["boot", "modemst1"])
        self.assertEqual(partitions[0].offset, 2048)
        self.assertEqual(partitions[0].size, 1024)

    def test_extract_partitions_skips_unsafe_by_default(self) -> None:
        tool = load_tool()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "disk.bin"
            out_dir = Path(tmp) / "split"
            write_synthetic_gpt(image)

            written = tool.extract_partitions(image, out_dir, names=["boot", "modemst1"])

            self.assertEqual([p.name for p in written], ["boot"])
            self.assertEqual((out_dir / "boot.img").read_bytes(), b"B" * 1024)
            self.assertFalse((out_dir / "modemst1.img").exists())

    def test_copy_exact_stops_after_requested_size(self) -> None:
        tool = load_tool()
        src = io.BytesIO(b"A" * 5 + b"Z" * 5)
        dst = io.BytesIO()

        tool.copy_exact(src, dst, size=5, chunk_size=2)

        self.assertEqual(dst.getvalue(), b"A" * 5)
        self.assertEqual(src.tell(), 5)


if __name__ == "__main__":
    unittest.main()
