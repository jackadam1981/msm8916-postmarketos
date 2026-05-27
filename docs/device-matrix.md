# Device Matrix

This matrix tracks candidates before hardware arrives. Values here are source-derived leads, not proof that a physical device matches.

## Status Values

| Status | Meaning |
| --- | --- |
| `source-candidate` | Exists in upstream source or a trusted reference, but no local hardware/firmware proof yet. |
| `firmware-identified` | Vendor firmware was inspected and IDs were extracted. |
| `hardware-identified` | Board markings, USB IDs, boot mode, and recovery path were recorded from a real device. |
| `lk2nd-selected` | lk2nd/lk1st selects the intended device node. |
| `linux-boots` | Standard Linux reaches userspace. |

## MSM8916 Modem-Stick Candidates

| Candidate | lk2nd compatible | lk2nd DTS | Source-derived match | Current status | First verification needed |
| --- | --- | --- | --- | --- | --- |
| Unknown 4G modem stick group: UFI_001B/C, UFI003_MB_V02, MF601 | `zhihe,various` | `msm8916-512mb-mtp.dts` | `QCOM_ID_MSM8916 0`, `QCOM_BOARD_ID_MTP 0x100`, shared cmdline panel match | `source-candidate` | Extract vendor DTS and confirm this board ID/cmdline. |
| UFI-001C / UFI-001B | `thwc,ufi001c` | `msm8916-512mb-mtp.dts` | Same bundle DTB as above; upstream recommends lk1st fixed compatible | `source-candidate` | Confirm board label, original boot image IDs, EDL key behavior on GPIO 37. |
| UFI003_MB_V02 | `zhihe,various` | `msm8916-512mb-mtp.dts` | Same generic MTP 512MB bucket as UFI_001B/C and MF601 | `source-candidate` | Confirm board marking and whether a fixed compatible exists outside current lk2nd. |
| MF601 | `zhihe,various` | `msm8916-512mb-mtp.dts` | Same generic MTP 512MB bucket; lk2nd lists reset GPIO 34 and optional WPS GPIO 107 for mis-detected MF601 | `source-candidate` | Confirm board marking, keys, and original firmware IDs. |
| UZ801 v3.0 | `yiming,uz801-v3` | `msm8916-512mb-mtp.dts` | Same bundle DTB plus DSI JDI 1080p cmdline match | `source-candidate` | Confirm panel cmdline and whether stock aboot has qhypstub/TZ incompatibility. |
| JZ0145 v33 | `xiaoxun,jz0145-v33` | `msm8916-512mb-mtp.dts` | Same bundle DTB plus DSI ST7796S 320p cmdline match | `source-candidate` | Confirm panel cmdline and EDL key behavior on GPIO 37. |
| UF896 | `thwc,uf896` | `msm8916-512mb-qrd-skuh.dts` | `QCOM_ID_MSM8916 0`, QRD SKUH board IDs with `0x100`/`0x104` variants | `source-candidate` | Extract vendor DTS and choose the exact QRD board tuple. |

## postmarketOS Baseline

For an MSM8916 modem stick, start from the generic pmaports path unless a device-specific package is later found:

| Layer | Candidate package/path | Why it matters |
| --- | --- | --- |
| Device package | `device/testing/device-qcom-msm8916` | Generic MSM8916/MSM8939 package with fastboot and lk2nd extlinux support. |
| Kernel package | `device/testing/linux-postmarketos-qcom-msm8916` | Uses the msm8916-mainline Linux fork and installs DTBs. |
| SoC package | `device/testing/soc-qcom-msm8916` | Common GPU/audio/remoteproc/modem support. |

## First Real-Hardware Checklist

1. Photograph PCB markings and labels.
2. Record USB IDs in normal, fastboot, and EDL modes.
3. Back up readable partitions before flashing.
4. Save original `boot.img` and full firmware package if available.
5. Extract DTB/DTS and record `qcom,msm-id`, `qcom,board-id`, `qcom,pmic-id`.
6. Compare extracted IDs with the lk2nd candidates above.
7. Prefer lk1st fixed-compatible testing where upstream says lk2nd cannot distinguish variants automatically.
