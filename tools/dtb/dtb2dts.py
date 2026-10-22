#!/usr/bin/env python3
"""Decompile a DTB back into DTS source.

This is the reverse of `dtc -I dts -O dtb`, implemented on top of the parser in
dtb_dump.py so it works without a toolchain (the project has no dtc, cpp or gcc
on Windows).

What survives the round trip: every node, every property, in the original
order, with the original values.  What does not: comments, #include structure,
label names and macro usage - none of that is stored in a DTB.  Treat the
output as evidence to read and diff, not as maintainable source.

Usage
    dtb2dts.py <input.dtb> [-o out.dts] [-q] [--no-phandle-map]
    dtb2dts.py --diff a.dtb b.dtb      compare two DTBs as DTS text

Value rendering follows dtc's conventions:
    empty property          ->  foo;
    NUL-terminated printable ->  foo = "a", "b";
    length % 4 == 0         ->  foo = <0x1 0x2>;
    anything else           ->  foo = [de ad be ef];
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dtb_dump import Node, parse  # noqa: E402

# Properties whose value is a list of cells even when it happens to look like a
# string (a 4-byte value of 0x00000001 is not the string "\x01").
# NOTE: nothing ending in -names belongs here.  clock-names / dma-names and
# friends are string lists; forcing them to cells turns "iface_clk" into
# 0x69666163, which is a silent and very confusing corruption.
CELL_PROPS = {
    "#address-cells", "#size-cells", "#interrupt-cells", "#clock-cells",
    "#gpio-cells", "#pwm-cells", "#phy-cells", "#dma-cells", "#sound-dai-cells",
    "#thermal-sensor-cells", "#iommu-cells", "#power-domain-cells",
    "#reset-cells", "#mbox-cells", "#cooling-cells", "#phandle-cells",
    "phandle", "linux,phandle", "interrupt-parent", "interrupts",
    "interrupts-extended", "reg", "clocks", "resets",
    "power-domains", "phys", "gpios", "gpio", "dmas",
    "iommus", "mboxes", "assigned-clocks",
    "assigned-clock-rates", "assigned-clock-parents", "ranges", "dma-ranges",
    "qcom,msm-id", "qcom,board-id", "qcom,pmic-id", "qcom,pmic-rev",
    "cpu-idle-states", "operating-points", "opp-hz", "opp-microvolt",
    "memory-region", "nvmem-cells",
}

# Suffixes that always mean "list of cells".
# -supply / -supplies are deliberately absent: a real supply is a single
# phandle cell, which the value heuristic already gets right (4 bytes, last
# byte non-NUL), while qcom,cdc-static-supplies is a downstream *string* list
# that would be shredded into hex bytes by a blanket suffix rule.
CELL_SUFFIXES = (
    "-cells", "-gpios", "-gpio",
    "-hz", "-rate", "-microvolt", "-microamp", "-bits",
)


def is_cell_prop(name: str) -> bool:
    # Hard guard: -names is always a string list.  Checked first so that a
    # future addition to CELL_PROPS cannot silently corrupt it again.
    if name.endswith("-names"):
        return False
    if name in CELL_PROPS:
        return True
    return name.endswith(CELL_SUFFIXES)


def escape(text: str) -> str:
    out = []
    for ch in text:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            out.append(f"\\x{ord(ch):02x}")
    return "".join(out)


def as_string_list(value: bytes) -> list[str] | None:
    """Return the NUL-separated strings, or None if this is not clean text."""
    if not value or not value.endswith(b"\x00"):
        return None
    body = value[:-1]
    if not body:
        return None
    parts = body.split(b"\x00")
    out = []
    for p in parts:
        if not p:
            # Two NULs in a row: empty string in the middle of a list is legal
            # but almost always means this is binary data, not text.
            return None
        try:
            txt = p.decode("utf-8")
        except UnicodeDecodeError:
            return None
        if any(not (32 <= ord(c) < 127) for c in txt):
            return None
        out.append(txt)
    return out


def render_value(name: str, value: bytes) -> str:
    """Render a property value the way dtc would."""
    if len(value) == 0:
        return ""  # boolean property

    if not is_cell_prop(name):
        strings = as_string_list(value)
        if strings is not None:
            return " = " + ", ".join(f'"{escape(s)}"' for s in strings)

    if len(value) % 4 == 0:
        cells = struct.unpack(f">{len(value) // 4}I", value)
        return " = <" + " ".join(f"0x{c:x}" for c in cells) + ">"

    return " = [" + " ".join(f"{b:02x}" for b in value) + "]"


def build_phandle_map(root: Node) -> dict[int, str]:
    """Map phandle value -> node path, for the annotation block at the end."""
    out = {}
    for node in root.walk():
        for key in ("phandle", "linux,phandle"):
            raw = node.props.get(key)
            if raw and len(raw) == 4:
                (val,) = struct.unpack(">I", raw)
                out.setdefault(val, node.path)
    return out


def node_header(node: Node) -> str:
    if node.parent is None:
        return "/"
    return node.name


def emit_node(node: Node, depth: int, lines: list[str], labels: dict[str, str]) -> None:
    indent = "\t" * depth
    header = node_header(node)
    label = labels.get(node.path)
    prefix = f"{label}: " if label else ""
    lines.append(f"{indent}{prefix}{header} {{")
    for name, value in node.props.items():
        lines.append(f"{indent}\t{name}{render_value(name, value)};")
    for child in node.children:
        emit_node(child, depth + 1, lines, labels)
    lines.append(f"{indent}}};")


def collect_labels(root: Node) -> dict[str, str]:
    """Recover label names if the DTB kept a __symbols__ node."""
    labels = {}
    for node in root.walk():
        if node.name != "__symbols__":
            continue
        for label, raw in node.props.items():
            path = as_string_list(raw)
            if path and len(path) == 1:
                labels[path[0]] = label
    return labels


def decompile(path: Path, quiet: bool = False, with_header: bool = True) -> str:
    root, hdr = parse(str(path))
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()

    labels = collect_labels(root)
    phandles = build_phandle_map(root)

    lines: list[str] = []
    if with_header:
        lines.append("// SPDX-License-Identifier: GPL-2.0-only")
        lines.append("/*")
        lines.append(f" * Decompiled from {path.name}")
        lines.append(f" *   size       {len(blob):,} B")
        lines.append(f" *   sha256     {digest}")
        lines.append(f" *   fdt        version {hdr['version']}, "
                     f"last_comp {hdr['last_comp_version']}, "
                     f"boot_cpuid {hdr['boot_cpuid_phys']}")
        lines.append(" *")
        lines.append(" * Produced by tools/dtb/dtb2dts.py.  Comments, #include structure")
        lines.append(" * and label names are not stored in a DTB, so they are absent here.")
        lines.append(" * Use this to read and diff the tree, not as source to maintain.")
        lines.append(" */")
        lines.append("")
    lines.append("/dts-v1/;")
    lines.append("")

    body: list[str] = []
    emit_node(root, 0, body, labels)
    lines.extend(body)

    if phandles and not quiet:
        lines.append("")
        lines.append("/*")
        lines.append(" * phandle -> node path")
        for val in sorted(phandles):
            lines.append(f" *   0x{val:<4x} {phandles[val]}")
        lines.append(" */")

    return "\n".join(lines) + "\n"


def cmd_diff(a: Path, b: Path) -> int:
    import difflib

    ta = decompile(a, quiet=True, with_header=False).splitlines()
    tb = decompile(b, quiet=True, with_header=False).splitlines()
    diff = list(difflib.unified_diff(ta, tb, str(a), str(b), lineterm="", n=3))
    if not diff:
        print(f"{a.name} and {b.name} decompile to identical DTS")
        return 0
    print("\n".join(diff))
    return 1


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2

    if args[0] == "--diff":
        if len(args) < 3:
            print("--diff needs two dtb files")
            return 2
        return cmd_diff(Path(args[1]), Path(args[2]))

    quiet = "-q" in args or "--no-phandle-map" in args
    rest = [a for a in args if a not in ("-q", "--no-phandle-map")]
    src = Path(rest[0])
    if not src.is_file():
        print(f"no such file: {src}")
        return 2

    out_path = None
    if "-o" in rest:
        idx = rest.index("-o")
        if idx + 1 >= len(rest):
            print("-o needs a path")
            return 2
        out_path = Path(rest[idx + 1])

    text = decompile(src, quiet=quiet)
    if out_path is None:
        sys.stdout.write(text)
        return 0

    out_path.write_text(text, encoding="utf-8", newline="\n")
    nodes = text.count("{") - 0
    print(f"wrote {out_path}  ({len(text):,} bytes, {text.count(chr(10)):,} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
