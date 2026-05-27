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
