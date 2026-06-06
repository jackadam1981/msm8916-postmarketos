# UFI003_MB_V02 设备树证据

本文记录三台 `UFI003_MB_V02` 真机在刷回 3.53G MIKO/UFI003 固件后的设备树证据。结论仅针对当前三台同丝印样本；外观相似或同类 MSM8916 棒子仍需单独核验。

## 结论

三台样本的运行态设备树关键字段一致，均落在 MSM8916 512MB MTP 桶：

| 字段 | 值 |
| --- | --- |
| `model` | `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` |
| `compatible` | `qcom,msm8916-mtp`, `qcom,msm8916`, `qcom,mtp` |
| `qcom,msm-id` | `<206 0>, <248 0>, <249 0>, <250 0>` |
| `qcom,board-id` | `<8 0x100>` |
| `memory/reg` | `<0 0x80000000 0 0x20000000>`，512MB |
| `uart@78af000/status` | `ok` |
| `sdhci@07824000/status` | `ok` |
| `sdhci@07864000/status` | `disabled` |
| panel bootargs | `mdss_mdp.panel=1:spi:0:qcom,mdss_spi_st7735s_128128_cmd` |

这与 lk2nd 上游 `msm8916-512mb-mtp.dts` 的 `qcom,board-id = <QCOM_BOARD_ID_MTP 0x100>` 和 `zhihe,various` 4G stick 分组一致。该上游 DTS 是 lk2nd 的匹配/元数据设备树，不是原厂 Android 的完整硬件设备树源码。

## 三台样本

| 编号 | ADB serial | 结果 |
| --- | --- | --- |
| UFI003-01 | `1db15d2` | 与三台公共字段一致 |
| UFI003-02 | `26e041bc` | 与三台公共字段一致 |
| UFI003-03 | `216ffcc1` | 与三台公共字段一致 |

三台对比文件：

```text
out/bringup/ufi003-device-tree-comparison-20260606.json
```

## 保存的设备树产物

从 UFI003-03 的 MIKO `boot.img` QCDT 中提取了匹配 `platform_id=206`、`variant_id=8`、`subtype_id=256` 的 DTB：

```text
out/bringup/ufi003-03/device-tree-20260606/ufi003-mb-v02.dtb
```

同内容的详细命名副本：

```text
out/bringup/ufi003-03/device-tree-20260606/ufi003-mb-v02-selected-board8-subtype0x100.dtb
```

SHA-256：

```text
7D4A2B2044C7073D27B5AF7162FFF83750E24475CA095E08D1B0557632F0FB7F
```

已将该 DTB 反编译为可读参考 DTS：

```text
out/bringup/ufi003-03/device-tree-20260606/ufi003-mb-v02.dts
```

反编译 DTS SHA-256：

```text
19D0F429D72E7878D3DDB4F953C428AF6E292D24672D3FEB9703D5BABB395D56
```

该文件用于审阅、对比和提炼硬件差异；它不是原厂源码的完整还原，也不应直接当作可维护的上游 DTS。注释、include 结构、符号名和人工组织方式在 DTB 中已经丢失，后续应从中提炼最小差异，落到 lk2nd/pmaports/mainline 风格的源码设备树中。

UFI003-03 的完整运行态 `/proc/device-tree` 已压缩保存：

```text
out/bringup/ufi003-03/device-tree-20260606/proc-device-tree.zip
```

SHA-256：

```text
FBEAC8C6EDFFEA62AFB0826CAE55C6C559267AE8DA7DC42CD72B40044386CD92
```

各机轻量摘要：

```text
out/bringup/ufi003-01/device-tree-20260606/runtime-device-tree-summary.json
out/bringup/ufi003-02/device-tree-20260606/runtime-device-tree-summary.json
out/bringup/ufi003-03/device-tree-20260606/runtime-device-tree-summary.json
```

## 和旧证据的关系

项目中较早的 `out/bringup/410-android/reports/selected-dtb-04-512mb-mtp.dtb` 与当前 `ufi003-mb-v02.dtb` 不是同一个二进制：

| 文件 | 大小 | SHA-256 |
| --- | ---: | --- |
| `out/bringup/410-android/reports/selected-dtb-04-512mb-mtp.dtb` | `144551` | `9D50F1CE1A0B55A917A96ECC5CAE8121E657B081899562741A33F8837F9AA601` |
| `out/bringup/ufi003-03/device-tree-20260606/ufi003-mb-v02.dtb` | `144837` | `7D4A2B2044C7073D27B5AF7162FFF83750E24475CA095E08D1B0557632F0FB7F` |

二者 root 级别的 model、compatible、`qcom,msm-id`、`qcom,board-id` 方向一致，说明它们属于同一 MSM8916 512MB MTP 桶；但当前应优先引用三台刷回 UFI003 固件后重新提取的 `ufi003-mb-v02.dtb`。

## 后续

- 对比 `ufi003-mb-v02.dts`、lk2nd `msm8916-512mb-mtp.dts` 和 pmaports/mainline 设备树，提炼 UFI003_MB_V02 真正需要维护的硬件差异。
- lk2nd 方向优先沿用 `msm8916-512mb-mtp.dtb` / `zhihe,various`，必要时再考虑为 `UFI003_MB_V02` 固定 compatible。
- 标准 Linux 方向先以 MSM8916 512MB MTP 桶作为 bring-up 基线，再逐项验证 USB、eMMC、modem、Wi-Fi、LED/GPIO。
