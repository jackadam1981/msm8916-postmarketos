# Flashing lk2nd

This page describes how lk2nd is normally flashed. Do not treat these commands as safe for a specific device until its boot mode, partition layout, original firmware backup, and recovery path are confirmed.

## Current Build

Build artifact:

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

Local copy:

```text
out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

SHA-256:

```text
02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0
```

## Before Flashing

Do these first:

1. Identify the exact board or candidate family.
2. Save the original `boot.img`.
3. Back up readable partitions.
4. Confirm whether the device can enter fastboot.
5. Confirm whether EDL recovery is available.
6. Confirm the boot partition name and size.

Stop if any of those are unknown.

## Normal Fastboot Flow

If the device has a working fastboot mode and the boot partition is confirmed:

```sh
fastboot devices
fastboot flash boot lk2nd-msm8916-ce7fc78.img
fastboot reboot
```

Some devices need raw flashing:

```sh
fastboot flash:raw boot lk2nd-msm8916-ce7fc78.img
```

If supported, a temporary boot test is safer than flashing:

```sh
fastboot boot lk2nd-msm8916-ce7fc78.img
```

Not every stock bootloader supports temporary boot.

## lk2nd Update Flow

After lk2nd is already running and exposes its own fastboot interface, updating lk2nd may use:

```sh
fastboot flash lk2nd lk2nd-msm8916-ce7fc78.img
```

This is only for the lk2nd fastboot environment, not necessarily the stock bootloader.

## EDL Flow

If the device must be written through EDL and the partition layout is confirmed:

```sh
edl w boot lk2nd-msm8916-ce7fc78.img
```

This requires a working EDL setup, a compatible programmer, and confidence that `boot` is the correct target partition.

## OpenStick Notes

For the OpenStick/UFI-style devices in this project, lk2nd likely covers several boards through the bundled MSM8916 QCDT image. That does not mean flashing is interchangeable.

The first real-device test should prefer:

1. Dump original firmware.
2. Extract downstream DTS and IDs.
3. Match against `docs/device-matrix.md`.
4. Try temporary boot if supported.
5. Flash only after recovery is proven.

## Recovery

Keep the original boot image available:

```sh
fastboot flash boot original-boot.img
```

or, if recovering through EDL:

```sh
edl w boot original-boot.img
```

Exact commands depend on the device and EDL tooling.
