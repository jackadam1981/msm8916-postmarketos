#!/usr/bin/env python3
"""Extract Qualcomm ID properties from a DTS file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROPERTIES = ("qcom,msm-id", "qcom,board-id", "qcom,pmic-id")


def parse_cells(value: str) -> list[int | str]:
    cells: list[int | str] = []
    for token in value.replace(",", " ").split():
        token = token.strip()
        if not token:
            continue
        try:
            cells.append(int(token, 0))
        except ValueError:
            cells.append(token)
    return cells


def extract_ids(dts_text: str) -> dict[str, list[list[int | str]]]:
    result: dict[str, list[list[int | str]]] = {name: [] for name in PROPERTIES}
    for prop in PROPERTIES:
        pattern = re.compile(rf"{re.escape(prop)}\s*=\s*((?:<[^>]*>\s*,?\s*)+);", re.MULTILINE)
        for match in pattern.finditer(dts_text):
            for group in re.findall(r"<([^>]*)>", match.group(1)):
                result[prop].append(parse_cells(group))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract qcom ID properties from a DTS file.")
    parser.add_argument("dts", type=Path, help="Path to a decompiled DTS file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    if not args.dts.is_file():
        parser.error(f"DTS file does not exist: {args.dts}")

    data = extract_ids(args.dts.read_text(encoding="utf-8", errors="replace"))
    print(json.dumps(data, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
