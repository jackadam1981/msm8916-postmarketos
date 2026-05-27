# Build lk2nd

This project builds lk2nd on the Linux build host, not in the Windows workspace.

## Build Host Path

```text
/home/jack/work/msm8916-standard-linux/third_party/lk2nd
```

## Minimal Packages

The build host uses Debian. Install only the required packages:

```sh
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  gcc-arm-none-eabi \
  binutils-arm-none-eabi \
  device-tree-compiler
```

`--no-install-recommends` avoids pulling the large `libstdc++-arm-none-eabi-newlib` package, which is not needed for the current lk2nd build.

## Build Command

```sh
cd /home/jack/work/msm8916-standard-linux/third_party/lk2nd
rm -rf build-lk2nd-msm8916
make -j$(nproc) TOOLCHAIN_PREFIX=arm-none-eabi- lk2nd-msm8916
```

## Variant Build Script

Use the project script when building all OpenStick/UFI candidates:

```sh
cd /home/jack/work/msm8916-standard-linux
sh scripts/build_lk2nd_variants.sh --list
sh scripts/build_lk2nd_variants.sh
```

The script names output files by board/profile and date:

```text
<board>-<build-target>-YYYYMMDD.<img|mbn>
```

The lk2nd commit is recorded in `manifest.psv` instead of the filename.

## Verified Build

Build input:

- lk2nd upstream: `https://github.com/msm8916-mainline/lk2nd.git`
- branch: `main`
- commit: `ce7fc78`
- compiler: `arm-none-eabi-gcc (15:14.2.rel1-1) 14.2.1 20241119`
- dtc: `DTC 1.7.2`

Generated outputs:

| File | Size | SHA-256 |
| --- | --- | --- |
| `build-lk2nd-msm8916/lk2nd.img` | 407K | `02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0` |
| `build-lk2nd-msm8916/qcdt.img` | 126K | `237decb1fc9d2594796031b9991f32bfd8ef19e837148e2c5887e0acd1731359` |

The generated QCDT image contains 44 DTBs, including:

- `msm8916-512mb-mtp.dtb`
- `msm8916-512mb-qrd-skuh.dtb`

The build artifact was copied on the build host to:

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

Do not flash this image to hardware until the device firmware, board IDs, partition layout, and recovery path are confirmed.

## Verified Variant Build

Output directory:

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-variants/
```

Local copy:

```text
out/lk2nd-variants/
```

Variant outputs built on `20260527`:

| File | Purpose | SHA-256 |
| --- | --- | --- |
| `generic-lk2nd-msm8916-20260527.img` | Generic lk2nd MSM8916 QCDT image | `02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0` |
| `zhihe-various-lk1st-msm8916-20260527.mbn` | Generic fixed lk1st profile for UFI_001B/C, UFI003_MB_V02, MF601 | `40a345f9f6e8a86de2cdf8919826976c809de2eaa628e61190bc4002483c3ab8` |
| `ufi001c-lk1st-msm8916-20260527.mbn` | Fixed lk1st profile for UFI-001B/C | `63c6f7f39ec634a30aa46018a61c25de5fbf21932b2a38d3afe7478069d6d805` |
| `uz801-v3-lk1st-msm8916-20260527.mbn` | Fixed lk1st profile for UZ801 v3.0 | `9d34e54f449054e45bde860a4c1334c32dd4a83178d9d61ffdfb4f9b4d44ea5c` |
| `jz0145-v33-lk1st-msm8916-20260527.mbn` | Fixed lk1st profile for JZ0145 v33 | `29a615f846534e33c82dfccb91ae3ea2c7419140a2fa1b836243572651665c45` |
| `uf896-lk1st-msm8916-20260527.mbn` | Fixed lk1st profile for UF896 | `0f7360db3ece77cc7ccb77698de9f5822f06a8653256ab989bc1506f03a1cbd5` |

`manifest.psv` records the source commit, bundle DTB, compatible string, and description for each output.
