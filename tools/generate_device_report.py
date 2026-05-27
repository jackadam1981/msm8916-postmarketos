#!/usr/bin/env python3
"""Generate a Markdown report from device metadata and optional extracted IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_scalar(value: str) -> object:
    if value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    try:
        return int(value, 0)
    except ValueError:
        return value


def read_simple_yaml(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    stack: list[tuple[int, object]] = [(-1, data)]
    last_key_for_indent: dict[int, tuple[dict[str, object], str]] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        if line.startswith("- "):
            value = parse_scalar(line[2:].strip())
            parent = stack[-1][1]
            if isinstance(parent, list):
                parent.append(value)
            else:
                owner, key = last_key_for_indent[indent]
                items: list[object] = []
                owner[key] = items
                stack.append((indent, items))
                items.append(value)
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        parent = stack[-1][1]
        if not isinstance(parent, dict):
            continue

        if value == "":
            next_container: object = {}
            parent[key] = next_container
            stack.append((indent, next_container))
            last_key_for_indent[indent + 2] = (parent, key)
        elif value == "[]":
            parent[key] = []
            last_key_for_indent[indent + 2] = (parent, key)
        else:
            parent[key] = parse_scalar(value)

    return data


def render_report(device: dict[str, object], extracted: dict[str, object] | None) -> str:
    lines = [
        f"# Device Report: {device.get('name', 'Unknown Device')}",
        "",
        f"- ID: `{device.get('id', 'unknown')}`",
        f"- Family: `{device.get('family', 'unknown')}`",
        f"- SoC: `{device.get('soc', 'unknown')}`",
        f"- Status: `{device.get('status', 'unknown')}`",
        "",
        "## Extracted Qualcomm IDs",
        "",
    ]

    if extracted:
        for key in ("qcom,msm-id", "qcom,board-id", "qcom,pmic-id"):
            lines.append(f"- `{key}`: `{json.dumps(extracted.get(key, []))}`")
    else:
        lines.append("No extracted ID JSON was provided.")

    lines.extend(
        [
            "",
            "## Next Checks",
            "",
            "1. Confirm these IDs against the original firmware source.",
            "2. Compare the values with upstream lk2nd MSM8916 device trees.",
            "3. Record boot and recovery evidence before flashing.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown report for an MSM8916 device.")
    parser.add_argument("device_yaml", type=Path, help="Path to a device YAML file")
    parser.add_argument("--ids-json", type=Path, help="Optional JSON output from extract_qcom_ids.py")
    parser.add_argument("--output", type=Path, help="Optional output Markdown path")
    args = parser.parse_args()

    if not args.device_yaml.is_file():
        parser.error(f"Device YAML does not exist: {args.device_yaml}")

    device = read_simple_yaml(args.device_yaml)
    extracted = None
    if args.ids_json:
        if not args.ids_json.is_file():
            parser.error(f"IDs JSON does not exist: {args.ids_json}")
        extracted = json.loads(args.ids_json.read_text(encoding="utf-8"))

    report = render_report(device, extracted)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
