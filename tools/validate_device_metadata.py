#!/usr/bin/env python3
"""Validate MSM8916 device metadata files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from generate_device_report import get_nested, read_simple_yaml


ALLOWED_STATUS = {
    "unknown",
    "source-candidate",
    "buildable-unverified",
    "firmware-identified",
    "hardware-identified",
    "lk2nd-selected",
    "linux-boots",
}

REQUIRED_TOP_LEVEL = (
    "schema",
    "id",
    "name",
    "aliases",
    "family",
    "soc",
    "status",
    "evidence",
    "hardware",
    "qcom_ids",
    "lk2nd",
    "linux",
    "firmware",
    "flashing",
    "notes",
)

REQUIRED_NESTED = (
    ("evidence", "firmware"),
    ("evidence", "upstream_refs"),
    ("evidence", "board_photos"),
    ("evidence", "serial_logs"),
    ("hardware", "board_markings"),
    ("hardware", "usb"),
    ("hardware", "storage"),
    ("hardware", "memory"),
    ("qcom_ids", "msm_id"),
    ("qcom_ids", "board_id"),
    ("qcom_ids", "pmic_id"),
    ("lk2nd", "status"),
    ("lk2nd", "dts"),
    ("lk2nd", "compatible"),
    ("linux", "status"),
    ("linux", "dts"),
    ("linux", "kernel_notes"),
    ("firmware", "known_files"),
    ("firmware", "extraction_notes"),
    ("flashing", "tested_methods"),
    ("flashing", "recovery_notes"),
)


def parse_variant_compatibles(script: Path) -> set[str]:
    text = script.read_text(encoding="utf-8")
    compatibles: set[str] = set()
    for line in text.splitlines():
        if line.count("|") < 5:
            continue
        parts = line.split("|")
        if len(parts) >= 4 and parts[3]:
            compatibles.add(parts[3])
    return compatibles


def has_nested(data: dict[str, object], *keys: str) -> bool:
    current: object = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    return True


def validate_device(path: Path, compatibles: set[str] | None) -> list[str]:
    errors: list[str] = []
    data = read_simple_yaml(path)

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"{path}: missing top-level key: {key}")

    for keys in REQUIRED_NESTED:
        if not has_nested(data, *keys):
            errors.append(f"{path}: missing nested key: {'.'.join(keys)}")

    if data.get("schema") != 1:
        errors.append(f"{path}: schema must be 1")

    device_id = data.get("id")
    if not isinstance(device_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", device_id):
        errors.append(f"{path}: id must be lowercase kebab-case")

    status = data.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"{path}: unsupported status: {status}")

    soc = data.get("soc")
    if soc != "msm8916":
        errors.append(f"{path}: soc must be msm8916")

    lk2nd_compatible = get_nested(data, "lk2nd", "compatible")
    if compatibles is not None and lk2nd_compatible and lk2nd_compatible not in compatibles:
        errors.append(f"{path}: lk2nd compatible is not built by variants script: {lk2nd_compatible}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MSM8916 device metadata files.")
    parser.add_argument("devices_dir", type=Path, help="Directory containing device YAML files")
    parser.add_argument("--variants-script", type=Path, help="Optional lk2nd variants shell script")
    args = parser.parse_args()

    if not args.devices_dir.is_dir():
        parser.error(f"Device directory does not exist: {args.devices_dir}")
    if args.variants_script and not args.variants_script.is_file():
        parser.error(f"Variants script does not exist: {args.variants_script}")

    compatibles = parse_variant_compatibles(args.variants_script) if args.variants_script else None
    yaml_files = sorted(path for path in args.devices_dir.glob("*.yaml") if path.is_file())
    errors: list[str] = []
    ids: dict[str, Path] = {}

    for path in yaml_files:
        data = read_simple_yaml(path)
        device_id = data.get("id")
        if isinstance(device_id, str):
            if device_id in ids:
                errors.append(f"{path}: duplicate id also used by {ids[device_id]}: {device_id}")
            ids[device_id] = path
        errors.extend(validate_device(path, compatibles))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Validated {len(yaml_files)} device metadata files")
    if compatibles is not None:
        print("All lk2nd compatibles are covered by build variants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
