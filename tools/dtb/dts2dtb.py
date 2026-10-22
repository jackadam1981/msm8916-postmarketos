#!/usr/bin/env python3
"""Compile a DTS file back into a flattened device tree blob.

This machine has no dtc, cpp or gcc, so the only way to prove that a
decompiled .dts really describes the original blob is to compile it back and
compare.  Only the subset of DTS that dtb2dts.py emits is supported:

    /dts-v1/;
    / { ... };

    node-name { ... };
    prop;
    prop = <0x1 0x2>;
    prop = "a", "b";
    prop = [de ad be ef];

No /include/, no labels, no &references, no /memreserve/, no /delete-node/.
That is not a limitation of the approach, it is exactly what survives a
round trip through a DTB - everything else lives only in source.

Usage:
    dts2dtb.py input.dts -o output.dtb
    dts2dtb.py --verify input.dts original.dtb     # exit 0 if identical

Exit codes:
    0  compiled (and identical, when --verify is used)
    1  parse or generation error
    2  compiled, but the result differs from the reference blob
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

FDT_MAGIC = 0xD00DFEED
FDT_BEGIN_NODE = 0x1
FDT_END_NODE = 0x2
FDT_PROP = 0x3
FDT_NOP = 0x4
FDT_END = 0x9

HEADER_SIZE = 40
VERSION = 17
LAST_COMP_VERSION = 16

IDENT_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    ",._+@#?*-"
)

ESCAPES = {
    "n": b"\n", "t": b"\t", "r": b"\r", "0": b"\0",
    "\\": b"\\", '"': b'"', "'": b"'", "a": b"\a", "b": b"\b",
    "f": b"\f", "v": b"\v",
}


class ParseError(Exception):
    pass


class Lexer:
    def __init__(self, text: str, path: str):
        self.t = text
        self.i = 0
        self.path = path

    def _line(self) -> int:
        return self.t.count("\n", 0, self.i) + 1

    def error(self, msg: str) -> ParseError:
        return ParseError(f"{self.path}:{self._line()}: {msg}")

    def skip(self) -> None:
        while self.i < len(self.t):
            c = self.t[self.i]
            if c.isspace():
                self.i += 1
            elif self.t.startswith("//", self.i):
                j = self.t.find("\n", self.i)
                self.i = len(self.t) if j < 0 else j + 1
            elif self.t.startswith("/*", self.i):
                j = self.t.find("*/", self.i + 2)
                if j < 0:
                    raise self.error("unterminated /* comment")
                self.i = j + 2
            else:
                return

    def peek(self) -> str:
        self.skip()
        return self.t[self.i] if self.i < len(self.t) else ""

    def take(self, s: str) -> None:
        self.skip()
        if not self.t.startswith(s, self.i):
            got = self.t[self.i:self.i + 20] or "<eof>"
            raise self.error(f"expected {s!r}, got {got!r}")
        self.i += len(s)

    def ident(self) -> str:
        self.skip()
        start = self.i
        while self.i < len(self.t) and self.t[self.i] in IDENT_CHARS:
            self.i += 1
        if self.i == start:
            raise self.error(f"expected an identifier, got {self.t[self.i:self.i+20]!r}")
        return self.t[start:self.i]

    def string(self) -> bytes:
        self.take('"')
        out = bytearray()
        while True:
            if self.i >= len(self.t):
                raise self.error("unterminated string")
            c = self.t[self.i]
            if c == '"':
                self.i += 1
                return bytes(out)
            if c == "\\":
                self.i += 1
                e = self.t[self.i] if self.i < len(self.t) else ""
                if e in ESCAPES:
                    out += ESCAPES[e]
                    self.i += 1
                elif e == "x":
                    out.append(int(self.t[self.i + 1:self.i + 3], 16))
                    self.i += 3
                else:
                    raise self.error(f"unknown escape \\{e}")
                continue
            out += c.encode("utf-8")
            self.i += 1


class Node:
    __slots__ = ("name", "props", "children")

    def __init__(self, name: str):
        self.name = name
        self.props: list[tuple[str, bytes]] = []
        self.children: list[Node] = []


def parse_value(lx: Lexer) -> bytes:
    """Parse one value: <cells>, "string" or [bytes]."""
    c = lx.peek()
    if c == "<":
        lx.take("<")
        cells = []
        while True:
            c = lx.peek()
            if c == ">":
                lx.take(">")
                break
            if c in ("", "{", "}", ";"):
                raise lx.error("unterminated cell list")
            tok = lx.ident()
            try:
                cells.append(int(tok, 0))
            except ValueError:
                raise lx.error(f"bad cell value {tok!r}")
        out = bytearray()
        for v in cells:
            if not -0x80000000 <= v <= 0xFFFFFFFF:
                raise lx.error(f"cell out of range: {v}")
            out += struct.pack(">I", v & 0xFFFFFFFF)
        return bytes(out)

    if c == '"':
        out = bytearray()
        out += lx.string() + b"\0"
        while lx.peek() == ",":
            # Adjacent strings are separate values, handled by the caller.
            break
        return bytes(out)

    if c == "[":
        lx.take("[")
        out = bytearray()
        while True:
            c = lx.peek()
            if c == "]":
                lx.take("]")
                break
            tok = lx.ident()
            if len(tok) != 2:
                raise lx.error(f"bad byte {tok!r}")
            out.append(int(tok, 16))
        return bytes(out)

    raise lx.error(f"expected a value, got {c!r}")


def parse_prop(lx: Lexer, name: str) -> bytes:
    lx.take("=")
    out = bytearray()
    first = True
    while True:
        if not first:
            lx.take(",")
        first = False
        c = lx.peek()
        if c == '"':
            out += lx.string() + b"\0"
        else:
            out += parse_value(lx)
        if lx.peek() != ",":
            break
    lx.take(";")
    return bytes(out)


def parse_node_body(lx: Lexer, node: Node) -> None:
    while True:
        c = lx.peek()
        if c == "":
            raise lx.error(f"unexpected end of file inside node {node.name!r}")
        if c == "}":
            lx.take("}")
            lx.take(";")
            return

        name = lx.ident()
        nxt = lx.peek()
        if nxt == "{":
            lx.take("{")
            child = Node(name)
            parse_node_body(lx, child)
            node.children.append(child)
        elif nxt == ";":
            lx.take(";")
            node.props.append((name, b""))
        elif nxt == "=":
            node.props.append((name, parse_prop(lx, name)))
        else:
            raise lx.error(f"expected '{{', ';' or '=' after {name!r}, got {nxt!r}")


def parse_dts(text: str, path: str) -> Node:
    lx = Lexer(text, path)
    lx.take("/dts-v1/")
    lx.take(";")
    if lx.peek() == "/memreserve/":
        raise lx.error("/memreserve/ is not supported by this compiler")
    lx.take("/")
    lx.take("{")
    root = Node("")
    parse_node_body(lx, root)
    if lx.peek() != "":
        raise lx.error(f"trailing data after root node: {lx.t[lx.i:lx.i+30]!r}")
    return root


def pad4(buf: bytearray) -> None:
    while len(buf) % 4:
        buf.append(0)


def build_struct(root: Node) -> tuple[bytes, bytes]:
    strings = bytearray()
    offsets: dict[str, int] = {}
    body = bytearray()

    def name_off(n: str) -> int:
        """Offset of a property name inside the strings block.

        dtc does not only deduplicate identical names, it also reuses an
        existing string when the name is a *suffix* of it - "reg" points
        into the middle of "qcom,reg".  Matching that keeps a round trip
        byte for byte identical instead of merely equivalent.
        """
        if n in offsets:
            return offsets[n]
        needle = n.encode("utf-8") + b"\0"
        pos = strings.find(needle)
        if pos >= 0:
            offsets[n] = pos
            return pos
        offsets[n] = len(strings)
        strings.extend(needle)
        return offsets[n]

    def emit(node: Node) -> None:
        body.extend(struct.pack(">I", FDT_BEGIN_NODE))
        body.extend(node.name.encode("utf-8") + b"\0")
        pad4(body)
        for pname, value in node.props:
            body.extend(struct.pack(">I", FDT_PROP))
            body.extend(struct.pack(">I", len(value)))
            body.extend(struct.pack(">I", name_off(pname)))
            body.extend(value)
            pad4(body)
        for child in node.children:
            emit(child)
        body.extend(struct.pack(">I", FDT_END_NODE))

    emit(root)
    body.extend(struct.pack(">I", FDT_END))
    return bytes(body), bytes(strings)


def build_dtb(root: Node, boot_cpuid: int = 0) -> bytes:
    struct_block, strings_block = build_struct(root)

    off_mem_rsvmap = HEADER_SIZE
    rsvmap = b"\0" * 16
    off_struct = off_mem_rsvmap + len(rsvmap)
    off_strings = off_struct + len(struct_block)
    totalsize = off_strings + len(strings_block)

    header = struct.pack(
        ">10I",
        FDT_MAGIC,
        totalsize,
        off_struct,
        off_strings,
        off_mem_rsvmap,
        VERSION,
        LAST_COMP_VERSION,
        boot_cpuid,
        len(strings_block),
        len(struct_block),
    )
    return header + rsvmap + struct_block + strings_block


def summarize(root: Node) -> tuple[int, int]:
    nodes = 0
    props = 0
    stack = [root]
    while stack:
        n = stack.pop()
        nodes += 1
        props += len(n.props)
        stack.extend(n.children)
    return nodes, props


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dts", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument(
        "--verify", type=Path, metavar="REFERENCE_DTB",
        help="compile, then compare byte for byte against this blob",
    )
    args = ap.parse_args()

    text = args.dts.read_text(encoding="utf-8")
    try:
        root = parse_dts(text, str(args.dts))
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    blob = build_dtb(root)
    nodes, props = summarize(root)

    if args.output:
        args.output.write_bytes(blob)
        print(f"wrote {args.output} ({len(blob):,} B, {nodes} nodes, {props} props)")

    if args.verify is None:
        if not args.output:
            sys.stdout.buffer.write(blob)
        return 0

    ref = args.verify.read_bytes()
    if blob == ref:
        print(f"IDENTICAL to {args.verify} ({len(blob):,} B)")
        return 0

    print(
        f"DIFFERS from {args.verify}: {len(blob):,} B vs {len(ref):,} B",
        file=sys.stderr,
    )
    limit = min(len(blob), len(ref))
    off = next((i for i in range(limit) if blob[i] != ref[i]), limit)
    print(f"first difference at offset {off:,} (0x{off:x})", file=sys.stderr)
    print(f"  compiled  {blob[off:off+32].hex(' ')}", file=sys.stderr)
    print(f"  reference {ref[off:off+32].hex(' ')}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
