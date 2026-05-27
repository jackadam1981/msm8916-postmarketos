#!/usr/bin/env python3
"""Generate a Markdown report from device metadata and optional extracted IDs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


QCOM_SYMBOLS = {
    "QCOM_ID_MSM8916": 206,
    "QCOM_BOARD_ID_MTP": 8,
}


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


def get_nested(data: dict[str, object], *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_id_tuple(value: object) -> tuple[int, ...] | None:
    if isinstance(value, int):
        return (value,)
    if not isinstance(value, str):
        return None

    cells: list[int] = []
    unresolved_symbol = False
    for token in re.findall(r"QCOM_BOARD_ID\([^)]*\)|QCOM_[A-Z0-9_]+|0x[0-9a-fA-F]+|\d+", value):
        token = token.strip()
        if token in QCOM_SYMBOLS:
            cells.append(QCOM_SYMBOLS[token])
        elif token.startswith("QCOM_"):
            unresolved_symbol = True
        else:
            cells.append(int(token, 0))

    if unresolved_symbol or not cells:
        return None
    return tuple(cells)


def extracted_id_set(extracted: dict[str, object] | None, key: str) -> set[tuple[int, ...]]:
    if not extracted:
        return set()
    values = extracted.get(key, [])
    result: set[tuple[int, ...]] = set()
    if isinstance(values, list):
        for item in values:
            if isinstance(item, list) and all(isinstance(cell, int) for cell in item):
                result.add(tuple(item))
    return result


def compare_property(candidate: dict[str, object], extracted: dict[str, object] | None, yaml_key: str, json_key: str) -> str:
    candidate_values = as_list(get_nested(candidate, "qcom_ids", yaml_key))
    extracted_values = extracted_id_set(extracted, json_key)
    if not candidate_values:
        return "未记录"
    if not extracted_values:
        return "无提取值"

    unresolved = False
    for value in candidate_values:
        normalized = normalize_id_tuple(value)
        if normalized is None:
            unresolved = True
            continue
        if normalized in extracted_values:
            return "直接匹配"

    return "需要人工复核" if unresolved else "未匹配"


def load_candidates(devices_dir: Path | None) -> list[dict[str, object]]:
    if devices_dir is None:
        return []
    candidates: list[dict[str, object]] = []
    for path in sorted(devices_dir.glob("*.yaml")):
        candidates.append(read_simple_yaml(path))
    return candidates


def render_candidates(candidates: list[dict[str, object]], extracted: dict[str, object] | None) -> list[str]:
    if not candidates:
        return []

    lines = [
        "",
        "## 候选板型矩阵",
        "",
        "| ID | 名称 | lk2nd compatible | DTS | msm-id | board-id | pmic-id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for candidate in candidates:
        lines.append(
            "| {id} | {name} | `{compatible}` | `{dts}` | {msm} | {board} | {pmic} |".format(
                id=candidate.get("id", "unknown"),
                name=candidate.get("name", "Unknown"),
                compatible=get_nested(candidate, "lk2nd", "compatible") or "unknown",
                dts=get_nested(candidate, "lk2nd", "dts") or "unknown",
                msm=compare_property(candidate, extracted, "msm_id", "qcom,msm-id"),
                board=compare_property(candidate, extracted, "board_id", "qcom,board-id"),
                pmic=compare_property(candidate, extracted, "pmic_id", "qcom,pmic-id"),
            )
        )

    lines.extend(
        [
            "",
            "说明：`直接匹配` 只表示 YAML 中可解析的 ID 元组和提取值一致；带宏或缺少原厂证据的条目仍需要结合 cmdline、分区表、硬件照片和启动日志复核。",
        ]
    )
    return lines


def render_report(
    device: dict[str, object],
    extracted: dict[str, object] | None,
    candidates: list[dict[str, object]] | None = None,
) -> str:
    lines = [
        f"# 设备报告：{device.get('name', 'Unknown Device')}",
        "",
        f"- ID: `{device.get('id', 'unknown')}`",
        f"- Family: `{device.get('family', 'unknown')}`",
        f"- SoC: `{device.get('soc', 'unknown')}`",
        f"- Status: `{device.get('status', 'unknown')}`",
        "",
        "## 提取到的 Qualcomm IDs",
        "",
    ]

    if extracted:
        for key in ("qcom,msm-id", "qcom,board-id", "qcom,pmic-id"):
            lines.append(f"- `{key}`: `{json.dumps(extracted.get(key, []))}`")
    else:
        lines.append("未提供提取出的 ID JSON。")

    lines.extend(render_candidates(candidates or [], extracted))

    lines.extend(
        [
            "",
            "## 下一步检查",
            "",
            "1. 用原厂固件来源复核这些 ID。",
            "2. 和上游 lk2nd MSM8916 设备树继续比对。",
            "3. 刷写前记录启动日志、分区表、备份和恢复证据。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown report for an MSM8916 device.")
    parser.add_argument("device_yaml", type=Path, help="Path to a device YAML file")
    parser.add_argument("--ids-json", type=Path, help="Optional JSON output from extract_qcom_ids.py")
    parser.add_argument("--devices-dir", type=Path, help="Optional directory with candidate device YAML files")
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

    if args.devices_dir and not args.devices_dir.is_dir():
        parser.error(f"Devices directory does not exist: {args.devices_dir}")

    candidates = load_candidates(args.devices_dir)
    report = render_report(device, extracted, candidates)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
