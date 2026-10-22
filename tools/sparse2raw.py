#!/usr/bin/env python3
"""Convert an Android sparse image to raw ext4.

If the input is not sparse, it is copied unchanged.
Usage:
    sparse2raw.py <input.img> [output.img]
If output is omitted, the input is overwritten in-place.
"""

import struct
import sys
import os
import tempfile
import shutil

SPARSE_HEADER_MAGIC = 0xED26FF3A
CHUNK_TYPE_RAW = 0xCAC1
CHUNK_TYPE_FILL = 0xCAC2
CHUNK_TYPE_DONT_CARE = 0xCAC3
CHUNK_TYPE_CRC = 0xCAC4


def convert(src_path: str, dst_path: str | None = None) -> str:
    if dst_path is None:
        dst_path = src_path

    with open(src_path, "rb") as f:
        header = f.read(28)
        if len(header) < 28:
            raise ValueError("file too small to be a sparse image")

        magic, = struct.unpack_from("<I", header, 0)
        if magic != SPARSE_HEADER_MAGIC:
            # Not sparse - copy if destination differs
            if src_path != dst_path:
                shutil.copy2(src_path, dst_path)
            return dst_path

        version_major, version_minor, file_hdr_sz, chunk_hdr_sz, blk_sz, \
            total_blks, total_chunks, image_checksum = struct.unpack_from(
                "<HHHHIIII", header, 4)

        if version_major != 1:
            raise ValueError(f"unsupported sparse version {version_major}.{version_minor}")

        # Write to a temp file first, then move (safer for in-place)
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(os.path.abspath(dst_path)) or ".",
            prefix=".sparse2raw_"
        )
        try:
            with os.fdopen(fd, "wb") as w:
                for _ in range(total_chunks):
                    chunk_hdr = f.read(12)
                    if len(chunk_hdr) < 12:
                        raise ValueError("truncated chunk header")
                    chunk_type, reserved, chunk_sz, total_sz = struct.unpack(
                        "<HHII", chunk_hdr)
                    data_sz = total_sz - 12

                    if chunk_type == CHUNK_TYPE_RAW:
                        data = f.read(data_sz)
                        if len(data) != data_sz:
                            raise ValueError("truncated raw chunk")
                        w.write(data)
                    elif chunk_type == CHUNK_TYPE_FILL:
                        fill_val = f.read(4)
                        if len(fill_val) != 4:
                            raise ValueError("truncated fill chunk")
                        w.write(fill_val * (chunk_sz * blk_sz // 4))
                    elif chunk_type == CHUNK_TYPE_DONT_CARE:
                        w.write(b"\x00" * (chunk_sz * blk_sz))
                    elif chunk_type == CHUNK_TYPE_CRC:
                        crc_data = f.read(data_sz)
                        if len(crc_data) != data_sz:
                            raise ValueError("truncated crc chunk")
                        # skip CRC
                    else:
                        # Unknown chunk: copy through as-is if data present
                        if data_sz:
                            w.write(f.read(data_sz))
                        else:
                            raise ValueError(f"unknown chunk type 0x{chunk_type:04x}")

            # Verify size against expected total blocks
            actual = os.path.getsize(tmp_path)
            expected = total_blks * blk_sz
            if actual != expected:
                raise ValueError(
                    f"size mismatch: expected {expected} bytes, got {actual}")

            # Atomic replace
            if sys.platform == "win32" and os.path.exists(dst_path):
                os.replace(tmp_path, dst_path)
            else:
                shutil.move(tmp_path, dst_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    return dst_path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = argv[1]
    dst = argv[2] if len(argv) > 2 else None
    out = convert(src, dst)
    action = "converted" if dst else "checked/converted"
    print(f"{action}: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
