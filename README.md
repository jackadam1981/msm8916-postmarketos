# MSM8916 PostmarketOS / Standard Linux Workbench

This repository tracks bring-up work for MSM8916 OpenStick/UFI-style devices before hardware is available.

The immediate goal is to reduce trial-and-error once a real device or vendor firmware arrives:

1. index relevant upstream source trees;
2. map known MSM8916 modem-stick candidates;
3. prepare firmware extraction and ID verification workflows;
4. document lk2nd and postmarketOS integration points.

## Current State

- Source checkouts live on the build host under `/home/jack/work/msm8916-standard-linux/third_party/`.
- `lk2nd`, `pmaports`, and `pmbootstrap` have been fetched for reference.
- No target hardware has been verified yet.
- No flashing commands should be treated as safe for a real device until its original firmware and board IDs are confirmed.

## Key Docs

- [Source Index](docs/source-index.md)
- [Device Matrix](docs/device-matrix.md)
- [Third-Party Sources](third_party/README.md)
- [Design Spec](docs/superpowers/specs/2026-05-27-msm8916-standard-linux-porting-design.md)

## Safety Rule

Similar MSM8916 dongles are not automatically interchangeable. A shell label or listing title is not enough. Treat a device as unknown until `qcom,msm-id`, `qcom,board-id`, boot mode, storage layout, and recovery path are verified from firmware or hardware evidence.
