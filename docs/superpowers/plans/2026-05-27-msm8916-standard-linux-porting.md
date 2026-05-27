# MSM8916 Standard Linux Porting Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable skeleton for an MSM8916/OpenStick/UFI standard Linux porting workbench.

**Architecture:** The project separates device knowledge, firmware extraction, lk2nd adaptation, and standard Linux bring-up. Firmware and generated output stay local and ignored, while templates, docs, and small standard-library tools are committed.

**Tech Stack:** Markdown documentation, YAML metadata, Python 3 standard library, PowerShell 5+.

---

## File Structure

- Create `.gitignore`: ignore local firmware, generated outputs, Python caches, temporary extraction files, and external source checkouts.
- Create `README.md`: project overview, quick workflow, safety warning, and current first-phase status.
- Create `docs/bringup-standard-linux.md`: standard Linux bring-up flow for MSM8916 devices.
- Create `docs/device-matrix.md`: table format and current device tracking process.
- Create `docs/firmware-extraction.md`: firmware and `boot.img` extraction process.
- Create `docs/flashing-and-recovery.md`: backup, flashing, and recovery notes.
- Create `docs/lk2nd-porting.md`: lk2nd adaptation workflow.
- Create `devices/README.md`: how device metadata is organized.
- Create `devices/templates/device.yaml`: canonical device metadata template.
- Create `devices/openstick/README.md`: notes for OpenStick-like MSM8916 dongles without claiming unverified IDs.
- Create `firmware/.gitkeep`: keep ignored firmware workspace visible.
- Create `out/.gitkeep`: keep ignored output workspace visible.
- Create `linux/README.md`: Linux bring-up workspace purpose.
- Create `linux/dts/README.md`: DTS staging notes.
- Create `linux/rootfs/README.md`: rootfs staging notes.
- Create `patches/lk2nd/README.md`: local lk2nd patch policy.
- Create `third_party/README.md`: external source policy.
- Create `tools/extract_qcom_ids.py`: parse DTS text for Qualcomm ID properties and emit JSON.
- Create `tools/generate_device_report.py`: render a Markdown report from the device YAML template plus optional extracted ID JSON.
- Create `tools/extract_bootimg.ps1`: validate firmware input and prepare extraction output directories with clear tool guidance.
- Create `tests/samples/sample-msm8916.dts`: small DTS fixture.

### Task 1: Repository Skeleton And Ignore Rules

**Files:**
- Create: `.gitignore`
- Create: `firmware/.gitkeep`
- Create: `out/.gitkeep`

- [ ] **Step 1: Create ignore rules**

Create `.gitignore` with:

```gitignore
# Local firmware and extraction products
firmware/*
!firmware/.gitkeep
out/*
!out/.gitkeep

# External source checkouts
third_party/lk2nd/
third_party/linux/

# Python
__pycache__/
*.py[cod]
.pytest_cache/

# Temporary files
*.tmp
*.log
*.img
*.bin
*.dtb
*.dtbo
*.dts.tmp
```

- [ ] **Step 2: Create kept workspace directories**

Create the directories and empty keep files:

```powershell
New-Item -ItemType Directory -Force -Path firmware,out | Out-Null
New-Item -ItemType File -Force -Path firmware/.gitkeep,out/.gitkeep | Out-Null
```

- [ ] **Step 3: Verify ignore behavior**

Run:

```powershell
git status --short
```

Expected if git is initialized: `.gitignore`, `firmware/.gitkeep`, and `out/.gitkeep` are visible; generated files under `firmware/` and `out/` would be ignored. If git is not initialized, expected output is `fatal: not a git repository`.

### Task 2: Top-Level Documentation

**Files:**
- Create: `README.md`
- Create: `docs/bringup-standard-linux.md`
- Create: `docs/device-matrix.md`
- Create: `docs/firmware-extraction.md`
- Create: `docs/flashing-and-recovery.md`
- Create: `docs/lk2nd-porting.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# MSM8916 Standard Linux Porting Workbench

This project is a bring-up workspace for MSM8916 OpenStick/UFI-style devices that may be portable to standard Linux.

The first goal is not to publish a complete distribution image. The first goal is to make device identification, firmware extraction, lk2nd adaptation, and Linux boot planning repeatable.

## Workflow

1. Back up the original device firmware and partitions.
2. Place local firmware artifacts under `firmware/`.
3. Extract downstream DT data from `boot.img` or vendor firmware.
4. Record verified device data under `devices/`.
5. Adapt lk2nd using patches under `patches/lk2nd/`.
6. Prepare standard Linux DTS, kernel, rootfs, and boot arguments under `linux/`.
7. Flash only after the recovery path is understood.

## Safety

MSM8916 dongles with similar shells can still use different boards, PMICs, panels, USB wiring, storage, or GPIO assignments. Treat every device as unknown until its firmware data and behavior are verified.

## Layout

- `devices/`: device metadata and family notes
- `docs/`: workflow documentation
- `firmware/`: local firmware input, ignored by git
- `linux/`: standard Linux bring-up notes and staging
- `out/`: generated reports and extracted artifacts, ignored by git
- `patches/lk2nd/`: local lk2nd patch notes and patch files
- `third_party/`: external source checkout guidance
- `tools/`: helper scripts
```

- [ ] **Step 2: Create bring-up doc**

Create `docs/bringup-standard-linux.md` with:

```markdown
# Standard Linux Bring-Up

The standard Linux path starts with identification, not flashing.

## Bring-Up Order

1. Verify the SoC family is MSM8916 or a compatible Qualcomm platform.
2. Extract the vendor device tree from original firmware.
3. Record `qcom,msm-id`, `qcom,board-id`, and `qcom,pmic-id`.
4. Confirm lk2nd can select the intended device tree.
5. Stage or write a Linux DTS that describes storage, USB, regulators, buttons, LEDs, Wi-Fi, and modem wiring.
6. Boot with a minimal rootfs before enabling complex services.

## Kernel Direction

Prefer mainline or close-to-mainline Linux sources when practical. Downstream Android kernels can be useful references, but they should not become the long-term project baseline unless a device cannot boot otherwise.

## Rootfs Direction

Keep rootfs choices separate from hardware bring-up. Debian, Alpine, OpenWrt, and custom initramfs images can all be useful once lk2nd and the kernel path are reliable.
```

- [ ] **Step 3: Create device matrix doc**

Create `docs/device-matrix.md` with:

```markdown
# Device Matrix

The device matrix tracks verified facts and open questions for MSM8916 OpenStick/UFI-style devices.

## Status Values

- `unknown`: no verified data yet
- `identified`: firmware IDs are extracted
- `lk2nd-candidate`: lk2nd DTS or patch is drafted
- `lk2nd-boots`: lk2nd selects the expected device tree
- `linux-boots`: standard Linux reaches userspace
- `stable`: repeatable boot and recovery process is documented

## Required Evidence

Do not add final IDs from memory. Record whether values came from extracted firmware, upstream lk2nd, upstream Linux DTS, board photos, or serial logs.

## Current Families

| Family | Notes | Metadata path |
| --- | --- | --- |
| OpenStick-like MSM8916 dongles | Similar devices from OpenStick and UFI projects; individual IDs must be verified. | `devices/openstick/` |
```

- [ ] **Step 4: Create firmware extraction doc**

Create `docs/firmware-extraction.md` with:

```markdown
# Firmware Extraction

Place firmware files in `firmware/`. This directory is ignored because vendor images can be large and redistributability is often unclear.

## Inputs

Common useful inputs:

- original `boot.img`
- full vendor firmware package
- partition backups from EDL or fastboot
- extracted DTB or DTS files

## Expected Flow

1. Copy input firmware to `firmware/<device-name>/`.
2. Run `tools/extract_bootimg.ps1` to validate paths and prepare output.
3. Use known boot image and DT tools to split the image.
4. Decompile DTB to DTS.
5. Run `tools/extract_qcom_ids.py` on the DTS.
6. Use `tools/generate_device_report.py` to compare extracted IDs with device metadata.

## External Tools

The first phase does not vendor binary extraction tools. Common tools include `unpackbootimg`, `magiskboot`, `dtc`, and Qualcomm EDL utilities.
```

- [ ] **Step 5: Create flashing and recovery doc**

Create `docs/flashing-and-recovery.md` with:

```markdown
# Flashing And Recovery

Do not flash a device until backups and recovery access are confirmed.

## Before Flashing

1. Save all readable partitions.
2. Record USB IDs and boot modes.
3. Confirm fastboot or EDL access.
4. Confirm the exact partition that will be written.
5. Keep the original boot image available.

## Recovery Notes

Many MSM8916 devices can be recovered through EDL if the correct programmer and partition layout are available. Recovery support varies by device and vendor firmware.

## Flashing Policy

Prefer reversible tests first. Boot temporary images when supported. Avoid overwriting vendor firmware until lk2nd selection and Linux boot behavior are understood.
```

- [ ] **Step 6: Create lk2nd doc**

Create `docs/lk2nd-porting.md` with:

```markdown
# lk2nd Porting

lk2nd is the first adaptation target because it can select a device tree and chainload Linux on MSM8916 devices.

## Porting Inputs

- extracted downstream DTS
- `qcom,msm-id`
- `qcom,board-id`
- `qcom,pmic-id`
- upstream lk2nd MSM8916 DTS examples
- serial logs or boot behavior

## Patch Strategy

Keep local changes under `patches/lk2nd/` so upstream lk2nd can be updated cleanly. A device patch should include the DTS change and any build-system entry needed for that DTS.

## Validation

The first validation target is correct device-tree selection. Linux boot is a later validation target.
```

### Task 3: Device Metadata Structure

**Files:**
- Create: `devices/README.md`
- Create: `devices/templates/device.yaml`
- Create: `devices/openstick/README.md`

- [ ] **Step 1: Create devices README**

```markdown
# Devices

Device files describe verified hardware facts and bring-up status. Similar-looking MSM8916 dongles must still get separate metadata when IDs or board behavior differ.

Use `devices/templates/device.yaml` for new entries.
```

- [ ] **Step 2: Create device YAML template**

```yaml
schema: 1
id: msm8916-example-device
name: Example MSM8916 Device
aliases:
  - Example Alias
family: openstick-like-msm8916
soc: msm8916
status: unknown
evidence:
  firmware: []
  upstream_refs: []
  board_photos: []
  serial_logs: []
hardware:
  board_markings: []
  usb:
    vendor_id: null
    product_id: null
    modes: []
  storage: unknown
  memory: unknown
qcom_ids:
  msm_id: []
  board_id: []
  pmic_id: []
lk2nd:
  status: unknown
  dts: null
  patch: null
linux:
  status: unknown
  dts: null
  kernel_notes: []
firmware:
  known_files: []
  extraction_notes: []
flashing:
  tested_methods: []
  recovery_notes: []
notes: []
```

- [ ] **Step 3: Create OpenStick family notes**

```markdown
# OpenStick-Like Devices

This folder is for MSM8916 USB dongles and pocket-router boards related to the OpenStick and UFI ecosystem.

Do not assume one device tree covers every device in this family. Add a specific metadata file only after extracting or otherwise verifying its Qualcomm IDs and hardware notes.
```

### Task 4: Linux, Patch, And Third-Party Workspaces

**Files:**
- Create: `linux/README.md`
- Create: `linux/dts/README.md`
- Create: `linux/rootfs/README.md`
- Create: `patches/lk2nd/README.md`
- Create: `third_party/README.md`

- [ ] **Step 1: Create Linux workspace README**

```markdown
# Linux Workspace

This directory tracks standard Linux bring-up notes and staging files.

Keep large kernel trees outside this repository or under ignored external checkout paths. Commit only small DTS experiments, notes, and reproducible configuration fragments.
```

- [ ] **Step 2: Create DTS README**

```markdown
# DTS Staging

Use this directory for small standard Linux DTS experiments and notes.

When a DTS becomes suitable for upstreaming, document its source evidence, tested hardware, and remaining gaps.
```

- [ ] **Step 3: Create rootfs README**

```markdown
# Rootfs Staging

Use this directory for rootfs notes and small configuration fragments.

Large rootfs images belong in `out/` or another ignored local path.
```

- [ ] **Step 4: Create lk2nd patches README**

```markdown
# lk2nd Patches

Store local lk2nd patches here.

Recommended patch names:

- `0001-msm8916-add-<device-id>.patch`
- `0002-msm8916-adjust-<device-id>-ids.patch`

Each patch should explain the firmware evidence used for `qcom,msm-id`, `qcom,board-id`, and `qcom,pmic-id`.
```

- [ ] **Step 5: Create third-party README**

```markdown
# Third-Party Sources

External source trees can be checked out here for local work, but large checkouts should stay uncommitted.

Suggested sources:

- `lk2nd`: MSM8916 bootloader adaptation work
- Linux kernel trees used for MSM8916 bring-up
- extraction utilities used to inspect vendor firmware
```

### Task 5: DTS Qualcomm ID Extractor

**Files:**
- Create: `tools/extract_qcom_ids.py`
- Create: `tests/samples/sample-msm8916.dts`

- [ ] **Step 1: Create sample DTS fixture**

```dts
/dts-v1/;

/ {
    model = "Sample MSM8916 Device";
    compatible = "qcom,msm8916";
    qcom,msm-id = <206 0>;
    qcom,board-id = <8 0>;
    qcom,pmic-id = <0x10009 0x1000a 0x0 0x0>;
};
```

- [ ] **Step 2: Create extractor implementation**

```python
#!/usr/bin/env python3
"""Extract Qualcomm ID properties from a DTS file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROPERTIES = ("qcom,msm-id", "qcom,board-id", "qcom,pmic-id")


def parse_cells(value: str) -> list[int]:
    cells: list[int] = []
    for token in value.replace(",", " ").split():
        token = token.strip()
        if not token:
            continue
        cells.append(int(token, 0))
    return cells


def extract_ids(dts_text: str) -> dict[str, list[list[int]]]:
    result: dict[str, list[list[int]]] = {name: [] for name in PROPERTIES}
    for prop in PROPERTIES:
        pattern = re.compile(rf"{re.escape(prop)}\s*=\s*<([^>]*)>\s*;", re.MULTILINE)
        for match in pattern.finditer(dts_text):
            result[prop].append(parse_cells(match.group(1)))
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
```

- [ ] **Step 3: Verify extractor help**

Run:

```powershell
python tools/extract_qcom_ids.py --help
```

Expected: usage text includes `Extract qcom ID properties from a DTS file.`

- [ ] **Step 4: Verify sample extraction**

Run:

```powershell
python tools/extract_qcom_ids.py tests/samples/sample-msm8916.dts --pretty
```

Expected JSON includes:

```json
{
  "qcom,board-id": [
    [
      8,
      0
    ]
  ],
  "qcom,msm-id": [
    [
      206,
      0
    ]
  ],
  "qcom,pmic-id": [
    [
      65545,
      65546,
      0,
      0
    ]
  ]
}
```

### Task 6: Device Report Generator

**Files:**
- Create: `tools/generate_device_report.py`

- [ ] **Step 1: Create report generator implementation**

```python
#!/usr/bin/env python3
"""Generate a Markdown report from device metadata and optional extracted IDs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_simple_yaml(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    stack: list[tuple[int, object]] = [(-1, data)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]
        if line.startswith("- "):
            value = line[2:].strip()
            if isinstance(parent, list):
                parent.append(parse_scalar(value))
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if not isinstance(parent, dict):
            continue

        if value == "":
            next_container: object = {}
            parent[key] = next_container
            stack.append((indent, next_container))
        elif value == "[]":
            parent[key] = []
        else:
            parent[key] = parse_scalar(value)

    return data


def parse_scalar(value: str) -> object:
    if value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    try:
        return int(value, 0)
    except ValueError:
        return value


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
```

- [ ] **Step 2: Verify report generator help**

Run:

```powershell
python tools/generate_device_report.py --help
```

Expected: usage text includes `Generate a Markdown report for an MSM8916 device.`

- [ ] **Step 3: Verify report generation**

Run:

```powershell
python tools/extract_qcom_ids.py tests/samples/sample-msm8916.dts --pretty > out/sample-ids.json
python tools/generate_device_report.py devices/templates/device.yaml --ids-json out/sample-ids.json --output out/sample-report.md
Get-Content out/sample-report.md
```

Expected: report starts with `# Device Report: Example MSM8916 Device` and includes all three qcom ID property names.

### Task 7: PowerShell Boot Image Extraction Entry Point

**Files:**
- Create: `tools/extract_bootimg.ps1`

- [ ] **Step 1: Create PowerShell script**

```powershell
param(
    [Parameter(Mandatory = $true)]
    [string]$InputImage,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = "out/extracted-bootimg"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputImage -PathType Leaf)) {
    throw "Input image does not exist: $InputImage"
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$resolvedInput = Resolve-Path -LiteralPath $InputImage
$resolvedOutput = Resolve-Path -LiteralPath $OutputDirectory

$manifest = @"
InputImage: $resolvedInput
OutputDirectory: $resolvedOutput

Next manual tools to run as available:
- unpackbootimg or magiskboot for boot image splitting
- dtc for DTB to DTS decompilation
- tools/extract_qcom_ids.py for qcom ID extraction
"@

$manifestPath = Join-Path $resolvedOutput "README.txt"
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8

Write-Host "Prepared extraction workspace: $resolvedOutput"
Write-Host "Manifest written: $manifestPath"
```

- [ ] **Step 2: Verify missing input behavior**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/extract_bootimg.ps1 -InputImage firmware/missing-boot.img
```

Expected: command fails with `Input image does not exist: firmware/missing-boot.img`.

- [ ] **Step 3: Verify workspace creation**

Run:

```powershell
New-Item -ItemType File -Force -Path firmware/sample-boot.img | Out-Null
powershell -ExecutionPolicy Bypass -File tools/extract_bootimg.ps1 -InputImage firmware/sample-boot.img -OutputDirectory out/sample-extract
Get-Content out/sample-extract/README.txt
```

Expected: output mentions `Prepared extraction workspace` and README includes `tools/extract_qcom_ids.py`.

### Task 8: Final Verification

**Files:**
- Read: all created files

- [ ] **Step 1: Run Python syntax checks**

Run:

```powershell
python -m py_compile tools/extract_qcom_ids.py tools/generate_device_report.py
```

Expected: no output and exit code `0`.

- [ ] **Step 2: Run end-to-end sample flow**

Run:

```powershell
python tools/extract_qcom_ids.py tests/samples/sample-msm8916.dts --pretty > out/sample-ids.json
python tools/generate_device_report.py devices/templates/device.yaml --ids-json out/sample-ids.json --output out/sample-report.md
Select-String -Path out/sample-report.md -Pattern 'qcom,msm-id','qcom,board-id','qcom,pmic-id'
```

Expected: all three property names are found.

- [ ] **Step 3: Inspect tree**

Run:

```powershell
Get-ChildItem -Recurse -File | Select-Object FullName
```

Expected: source docs and scripts are present; local generated outputs may exist under ignored `out/`.

- [ ] **Step 4: Commit if git is initialized**

Run:

```powershell
git status --short
```

If git is initialized, commit with:

```powershell
git add .gitignore README.md docs devices linux patches third_party tools tests firmware/.gitkeep out/.gitkeep
git commit -m "chore: initialize msm8916 linux porting workbench"
```

If git is not initialized, record that commit was skipped because the workspace has no `.git` directory.

---

## Self-Review

- Spec coverage: the plan covers project skeleton, ignored local workspaces, documentation, device metadata, extraction entry points, report generation, and verification.
- Placeholder scan: no task uses TBD/TODO/fill-in placeholders.
- Type consistency: Python function names and command paths are consistent across tasks.
