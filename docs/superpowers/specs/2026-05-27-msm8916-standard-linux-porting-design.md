# MSM8916 Standard Linux Porting Workbench Design

## Goal

Build a blank-project workbench for porting MSM8916 OpenStick/UFI-style devices to standard Linux. The project should make it easy to identify similar devices, extract downstream firmware device-tree data, adapt lk2nd, and document safe flashing and recovery paths.

## Scope

The first implementation phase creates the project skeleton, documentation, device metadata format, and extraction-tool entry points. It does not build a full Linux distribution image yet. It prepares the repository so device-specific data and firmware artifacts can be added incrementally.

## Architecture

The project is organized around four flows:

1. Device discovery: maintain a device matrix and per-device metadata files under `devices/`.
2. Firmware extraction: place local firmware under ignored `firmware/`, then run scripts under `tools/` to inspect `boot.img` and extract Qualcomm IDs.
3. lk2nd adaptation: keep upstream lk2nd external to project data, with local adaptation notes and patches under `patches/lk2nd/`.
4. Standard Linux bring-up: document kernel, DTS, rootfs, boot arguments, and recovery expectations under `linux/` and `docs/`.

## Directory Layout

```text
Msm8916/
  README.md
  .gitignore
  docs/
    bringup-standard-linux.md
    device-matrix.md
    firmware-extraction.md
    flashing-and-recovery.md
    lk2nd-porting.md
    superpowers/
      specs/
        2026-05-27-msm8916-standard-linux-porting-design.md
      plans/
  devices/
    README.md
    templates/
      device.yaml
    openstick/
      README.md
  firmware/
    .gitkeep
  linux/
    README.md
    dts/
      README.md
    rootfs/
      README.md
  out/
    .gitkeep
  patches/
    lk2nd/
      README.md
  third_party/
    README.md
  tools/
    extract_bootimg.ps1
    extract_qcom_ids.py
    generate_device_report.py
```

`firmware/` and `out/` are local working directories and should stay ignored except for `.gitkeep`. Firmware binaries, extracted DTBs, generated reports, and built images should not be committed.

## Device Metadata

Device metadata uses YAML because it is readable during hardware bring-up. The template captures:

- human name and aliases
- SoC family
- known board markings
- USB identity if known
- downstream `qcom,msm-id`, `qcom,board-id`, and `qcom,pmic-id`
- source firmware file names
- lk2nd DTS status
- Linux DTS status
- flashing notes and recovery notes

The first repository version provides a template, not final per-device claims. Device files should be added only when values are verified from firmware or trusted upstream references.

## Tooling

The initial scripts are intentionally conservative:

- `extract_bootimg.ps1` validates input paths and creates an output folder for extracted artifacts. It documents required external tools instead of silently inventing binary parsing.
- `extract_qcom_ids.py` parses DTS text and reports Qualcomm ID properties in JSON.
- `generate_device_report.py` combines a device YAML file and optional extracted ID JSON into a Markdown report.

The scripts should run on Windows from PowerShell, because the current workspace is on Windows. Python scripts should use only the standard library in the first phase.

## Documentation

The docs should explain the workflow in order:

1. Back up original firmware and partitions.
2. Extract downstream DT data from firmware.
3. Compare IDs against the device matrix.
4. Add or adjust lk2nd DTS patches.
5. Prepare a standard Linux boot path.
6. Flash cautiously and keep recovery options available.

The docs should avoid pretending that all MSM8916 dongles are interchangeable. Similar devices must be treated as candidates until their IDs and hardware behavior are verified.

## Testing And Verification

Initial verification should cover:

- Python script help output.
- Python parsing of a small sample DTS string.
- report generation from the device template.
- path validation behavior in the PowerShell script.

No hardware flashing is part of automated testing.

## Risks

Wrong board IDs or PMIC IDs can make lk2nd select the wrong device tree. Wrong flashing commands can soft-brick a device. The project should repeatedly bias toward backup, inspection, and reversible steps.
