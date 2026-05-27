# Source Index

This document records the source trees that are useful before we have real hardware.

## Build Host Workspace

```text
/home/jack/work/msm8916-standard-linux/third_party/
```

| Source | Local path | Upstream | State |
| --- | --- | --- | --- |
| lk2nd | `lk2nd` | `https://github.com/msm8916-mainline/lk2nd.git` | shallow git clone, `main`, `ce7fc78` |
| pmaports | `pmaports` | `https://gitlab.postmarketos.org/postmarketOS/pmaports.git` | shallow git clone, `main`, `02ad959` |
| pmbootstrap | `pmbootstrap` | `https://gitlab.postmarketos.org/postmarketOS/pmbootstrap` | `main` archive, no git history |

The Linux kernel tree has not been cloned yet. The pmaports package currently points at `https://github.com/msm8916-mainline/linux` with tags like `v6.12.1-msm8916`; clone this only after we choose the first concrete target.

## lk2nd MSM8916 Map

Important paths:

| Purpose | Path |
| --- | --- |
| MSM8916 DTS directory | `lk2nd/device/dts/msm8916/` |
| MSM8916 DTS build list | `lk2nd/device/dts/msm8916/rules.mk` |
| lk2nd MSM8916 project | `project/lk2nd-msm8916.mk` |
| lk1st MSM8916 project | `project/lk1st-msm8916.mk` |
| MSM8916 platform code | `platform/msm8916/` |
| MSM8916 target code | `target/msm8916/` |

Modem-stick candidates already present upstream:

| DTS | Model / compatible | Match data | Notes |
| --- | --- | --- | --- |
| `msm8916-512mb-mtp.dts` | `Unknown 4G Modem Stick`, `zhihe,various` | `qcom,msm-id = <QCOM_ID_MSM8916 0>`, `qcom,board-id = <QCOM_BOARD_ID_MTP 0x100>` | Generic bucket for UFI_001B/C, UFI003_MB_V02, MF601. Upstream says automatic distinction is difficult because cmdline is shared. |
| `msm8916-512mb-mtp.dts` | `ufi-001c/ufi-001b 4G Modem Stick`, `thwc,ufi001c` | same bundle DTB | Intended for `lk1st` with `LK2ND_COMPATIBLE="thwc,ufi001c"`. |
| `msm8916-512mb-mtp.dts` | `UFI003_MB_V02` | same generic `zhihe,various` bucket | Mentioned in upstream comments, but current lk2nd does not expose a separate compatible node for it. |
| `msm8916-512mb-mtp.dts` | `MF601` | same generic `zhihe,various` bucket | Mentioned in upstream comments; lk2nd lists reset/WPS key GPIOs for a mis-detected MF601 case. |
| `msm8916-512mb-mtp.dts` | `uz801 v3.0 4G Modem Stick`, `yiming,uz801-v3` | same bundle DTB plus cmdline match | Upstream notes stock aboot may be incompatible with qhypstub/db410c TZ firmware; prefer lk1st if possible. |
| `msm8916-512mb-mtp.dts` | `JZ0145 v33 4G Modem Stick`, `xiaoxun,jz0145-v33` | same bundle DTB plus cmdline match | Has an EDL key on GPIO 37 in lk2nd metadata. |
| `msm8916-512mb-qrd-skuh.dts` | `uf896 4G Modem Stick`, `thwc,uf896` | `qcom,msm-id = <QCOM_ID_MSM8916 0>`, multiple QRD SKUH board IDs with subtype `0x100`/`0x104` | Intended for `lk1st` with `LK2ND_COMPATIBLE="thwc,uf896"`. |

Upstream `rules.mk` already includes both `msm8916-512mb-mtp.dtb` and `msm8916-512mb-qrd-skuh.dtb` in `QCDTBS`, so the first task with real firmware is likely identification and selection, not necessarily writing a new lk2nd DTS from scratch.

## pmaports MSM8916 Map

Important paths:

| Purpose | Path |
| --- | --- |
| Generic MSM8916 device package | `device/testing/device-qcom-msm8916/` |
| MSM8916 kernel package | `device/testing/linux-postmarketos-qcom-msm8916/` |
| MSM8916 common SoC package | `device/testing/soc-qcom-msm8916/` |

Observed package details:

| Package | Key facts |
| --- | --- |
| `device-qcom-msm8916` | Generic package for MSM8916/MSM8939 devices, `aarch64`, fastboot flash method, extlinux support for lk2nd, `deviceinfo_dtb_extlinux="qcom/msm8*16-* qcom/msm8*39-* qcom/apq8016-* apq8039-*"`, `deviceinfo_partition_type="msdos"` because lk2nd does not support GPT for subpartitions/SD cards yet. |
| `linux-postmarketos-qcom-msm8916` | Kernel package uses `https://github.com/msm8916-mainline/linux`, package version `6.12.1`, tag pattern `v6.12.1-msm8916`, supports `aarch64` and `armv7`. |
| `soc-qcom-msm8916` | Common SoC package includes Adreno A306 quirks, UCM audio packaging, remoteproc/modem support, q6voiced config, and WirePlumber S16_LE workaround. |

## No-Hardware Priorities

1. Keep expanding this source index as we inspect upstream.
2. Add device metadata templates for each lk2nd modem-stick candidate.
3. Build scripts that can accept a vendor `boot.img` later and extract `qcom,*-id`.
4. Prepare a checklist for the first real device: photos, USB IDs, boot modes, partition backup, DT extraction, lk2nd selection, postmarketOS package choice.
