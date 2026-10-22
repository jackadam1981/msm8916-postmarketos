#!/usr/bin/env python3
"""Minimal Flattened Device Tree (DTB) parser / differ.

No external dependencies.  Used to compare a vendor/extracted DTB against the
one postmarketOS builds from upstream sources, without needing `dtc`.

Usage:
    dtb_dump.py dump  <file.dtb>              # human readable tree
    dtb_dump.py json  <file.dtb>              # canonical JSON
    dtb_dump.py diff  <a.dtb> <b.dtb>         # structural diff

Only the structure block is decoded; property values are kept as raw bytes and
rendered the way `dtc` would for the common cases (strings, u32 cells, empty).
"""

from __future__ import annotations

import json
import struct
import sys
from typing import Any

FDT_MAGIC = 0xD00DFEED
FDT_BEGIN_NODE = 1
FDT_END_NODE = 2
FDT_PROP = 3
FDT_NOP = 4
FDT_END = 9


def _align4(n: int) -> int:
    return (n + 3) & ~3


class Node:
    __slots__ = ("name", "props", "children", "parent")

    def __init__(self, name: str, parent: "Node | None" = None):
        self.name = name
        self.props: dict[str, bytes] = {}
        self.children: list["Node"] = []
        self.parent = parent

    @property
    def path(self) -> str:
        if self.parent is None:
            return "/"
        parts = []
        cur: Node | None = self
        while cur is not None and cur.parent is not None:
            parts.append(cur.name)
            cur = cur.parent
        return "/" + "/".join(reversed(parts))

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def parse(path: str) -> tuple[Node, dict[str, Any]]:
    with open(path, "rb") as f:
        blob = f.read()

    if len(blob) < 40:
        raise ValueError(f"{path}: too small to be a DTB")

    # FDT header, see Documentation/devicetree/booting-without-of.rst
    #  0 magic | 4 totalsize | 8 off_dt_struct | 12 off_dt_strings
    # 16 off_mem_rsvmap | 20 version | 24 last_comp_version | 28 boot_cpuid_phys
    # 32 size_dt_strings | 36 size_dt_struct
    (magic, totalsize, off_struct, off_strings, off_rsvmap,
     version, last_comp, boot_cpuid, size_strings, size_struct) = struct.unpack_from(">10I", blob, 0)

    if magic != FDT_MAGIC:
        raise ValueError(f"{path}: bad magic 0x{magic:08x} (expected 0x{FDT_MAGIC:08x})")

    strings = blob[off_strings:off_strings + size_strings]
    hdr = {
        "totalsize": totalsize,
        "version": version,
        "last_comp_version": last_comp,
        "boot_cpuid_phys": boot_cpuid,
        "off_dt_struct": off_struct,
        "off_dt_strings": off_strings,
        "size_dt_strings": size_strings,
        "off_mem_rsvmap": off_rsvmap,
    }

    def get_string(off: int) -> str:
        end = strings.find(b"\x00", off)
        if end < 0:
            end = len(strings)
        return strings[off:end].decode("utf-8", "replace")

    root = Node("", None)
    cur = root
    pos = off_struct
    end = off_struct + (size_struct or totalsize)

    while pos < end:
        (tok,) = struct.unpack_from(">I", blob, pos)
        pos += 4

        if tok == FDT_BEGIN_NODE:
            nul = blob.find(b"\x00", pos)
            name = blob[pos:nul].decode("utf-8", "replace")
            pos = _align4(nul + 1)
            if cur is root and not root.children and name == "":
                # root node: reuse it
                continue
            node = Node(name, cur)
            cur.children.append(node)
            cur = node
        elif tok == FDT_END_NODE:
            if cur.parent is not None:
                cur = cur.parent
        elif tok == FDT_PROP:
            length, nameoff = struct.unpack_from(">II", blob, pos)
            pos += 8
            value = blob[pos:pos + length]
            pos = _align4(pos + length)
            cur.props[get_string(nameoff)] = value
        elif tok == FDT_NOP:
            continue
        elif tok == FDT_END:
            break
        else:
            raise ValueError(f"{path}: unknown token 0x{tok:x} at offset {pos - 4}")

    return root, hdr


def render(value: bytes) -> Any:
    """Best-effort rendering, similar to what dtc prints."""
    if len(value) == 0:
        return True  # boolean property
    # A NUL-separated string list (one or more strings, trailing NUL).
    if value.endswith(b"\x00"):
        try:
            txt = value[:-1].decode("utf-8")
        except UnicodeDecodeError:
            txt = None
        if txt is not None and txt and all(
            32 <= ord(c) < 127 or c in "\t\n\x00" for c in txt
        ):
            return txt.split("\x00")
    if len(value) % 4 == 0:
        return [f"0x{x:x}" for x in struct.unpack(f">{len(value) // 4}I", value)]
    return value.hex()


def to_json(root: Node, hdr: dict[str, Any]) -> dict[str, Any]:
    def conv(node: Node) -> dict[str, Any]:
        return {
            "path": node.path,
            "props": {k: render(v) for k, v in node.props.items()},
            "children": [conv(c) for c in node.children],
        }
    return {"header": hdr, "tree": conv(root)}


def flat(node: Node) -> dict[str, dict[str, Any]]:
    out = {}
    for n in node.walk():
        out[n.path] = {k: render(v) for k, v in n.props.items()}
    return out


def cmd_dump(path: str) -> None:
    root, hdr = parse(path)
    print(f"# {path}")
    print(f"# totalsize={hdr['totalsize']} version={hdr['version']} "
          f"strings={hdr['size_dt_strings']}B")
    for n in root.walk():
        depth = 0 if n.parent is None else n.path.count("/")
        print(f"{'  ' * depth}{n.name or '/'} {{")
        for k, v in n.props.items():
            r = render(v)
            if r is True:
                print(f"{'  ' * (depth + 1)}{k};")
            elif isinstance(r, list) and r and isinstance(r[0], str) and not r[0].startswith("0x"):
                print(f"{'  ' * (depth + 1)}{k} = {r!r};")
            else:
                print(f"{'  ' * (depth + 1)}{k} = {r};")


def cmd_json(path: str) -> None:
    root, hdr = parse(path)
    json.dump(to_json(root, hdr), sys.stdout, indent=1, ensure_ascii=False)
    print()


def cmd_diff(a: str, b: str) -> None:
    ra, ha = parse(a)
    rb, hb = parse(b)
    fa, fb = flat(ra), flat(rb)

    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))

    print(f"A = {a}  ({ha['totalsize']} B, {len(fa)} nodes)")
    print(f"B = {b}  ({hb['totalsize']} B, {len(fb)} nodes)")
    print()

    if only_a:
        print(f"--- only in A ({len(only_a)}) ---")
        for p in only_a:
            print("  -", p)
        print()
    if only_b:
        print(f"--- only in B ({len(only_b)}) ---")
        for p in only_b:
            print("  +", p)
        print()

    diffs = 0
    for p in sorted(set(fa) & set(fb)):
        pa, pb = fa[p], fb[p]
        keys = sorted(set(pa) | set(pb))
        for k in keys:
            va, vb = pa.get(k, "<absent>"), pb.get(k, "<absent>")
            if va != vb:
                diffs += 1
                print(f"~ {p}:{k}")
                print(f"    A: {va}")
                print(f"    B: {vb}")
    print()
    print(f"property differences: {diffs}")
    if not only_a and not only_b and not diffs:
        print("STRUCTURALLY IDENTICAL")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "dump":
        cmd_dump(argv[2])
    elif cmd == "json":
        cmd_json(argv[2])
    elif cmd == "diff":
        if len(argv) < 4:
            print(__doc__)
            return 2
        cmd_diff(argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
