# QRZL903-1 设备清单

本文用于记录两台 `QRZL903-1` 设备的可区分信息、备份位置和恢复状态，避免样本之间的身份分区、整盘备份和固件状态混淆。

## 记录原则

- 每台机器刷写前先备份 `modemst1`、`modemst2`、`fsg`、`fsc`，条件允许时再备份整盘 eMMC。
- 不要把一台机器的 `modemst1/2`、`fsg/fsc`、`persist`、`userdata` 直接写到另一台机器上。
- `IMEI(RIL)` 以 Android `dumpsys iphonesubinfo` 返回的 `Device ID` 为准；`persist.wlan.imei.fromnv` 只作为厂商属性记录。
- `QRZL903-02` 的原厂 Android 整盘备份可作为恢复基线，但恢复其他个体时必须注入或保留目标机器自己的校准/身份分区。
- `MIKO-QRZL903-1.bin` 比两台实机 eMMC 大 8MiB，不作为整盘直写来源。

## 设备列表

| 编号 | PCB | 当前固件/状态 | ADB/USB 序列号 | EDL serial | IMEI(RIL) | 厂商 NV IMEI | Wi-Fi MAC(NV) | USB/network | eMMC | 备份位置 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QRZL903-01 | `QRZL903-1` | Android/MTP GPT，`UFI_XG_WFSER_HW03CTDD_220615` | `a33fbfc` | `0x017a302b` | `864405028082598` | `000000041775022` | `5c:a0:00:3c:a7:85` | `192.168.100.1:80`、`:5555` | `3867148288` bytes | `out/bringup/qrzl903-01/` | 曾是 OpenWrt/Linux GPT；已用 02 原厂备份加 01 自身 `modemst1/2/fsc/fsg` 恢复 Android |
| QRZL903-02 | `QRZL903-1` | 原厂 Android/MTP GPT，`UFI_XG_WFSER_HW03CTDD_220615` | `d0b1d17` | `0x0b723827` | `861386074067431` | `000000041775022` | `5c:a0:00:3c:80:2c` | `192.168.100.1`，TCP ADB `5555` | `3867148288` bytes | `out/bringup/qrzl903-02/` | 本项目持有的原厂 Android 基准样本，已做 EDL 整盘只读备份 |

## QRZL903-01 历史状态

样本 01 初始接入时为 Linux/OpenWrt 风格 GPT：

```text
cdt, sbl1, rpm, tz, hyp, sec, modemst1, modemst2, fsc, fsg, aboot, boot, devinfo, rootfs
```

历史状态备份：

```text
out/bringup/qrzl903-01/edl-20260606/
out/bringup/qrzl903-01/edl-20260606/partitions/
```

关键历史备份哈希：

| 文件 | SHA-256 |
| --- | --- |
| `boot.bin` | `62760820fdec0bb42ed2f8364ae94ec16b6fc1b74c59e0906b7f90b8f04f4770` |
| `rootfs.bin` | `f985cf214dbd7e25fa595692854400627e4a5d7a4094b6533780224ea5dcfbf7` |
| `modemst1.bin` | `43cf140de89768785c26f57af4e216d7c43812eef778698ec4cd41fef9fbf785` |
| `modemst2.bin` | `c0fbfb2b40099f3b46a143485ab3d4b29ddacae85444d3994ad53ba7da11e12a` |
| `fsg.bin` | `703676e69645f597702fe8d5b114f1bc7303e5c66b620c545ac6669396c59237` |

历史 OpenWrt boot DTB：

```text
out/bringup/qrzl903-01/device-tree-20260606/qrzl903-01-current-boot.dtb
out/bringup/qrzl903-01/device-tree-20260606/qrzl903-01-current-boot.dts
```

| 文件 | SHA-256 |
| --- | --- |
| `qrzl903-01-current-boot.dtb` | `f140983483b78a99f60071ed34ceddab960e3ae9791076ad2395cd11bf2fa5de` |
| `qrzl903-01-current-boot.dts` | `0bc5cf53af74cea435b684c119845d1641c668c9b5714b8891bfe1951e95c73e` |

该历史 DTB root：

| 字段 | 值 |
| --- | --- |
| `model` | `ufi-001c 4G Modem Stick` |
| `compatible` | `thwc,ufi001c`, `qcom,msm8916` |

## QRZL903-01 Android 恢复

恢复镜像：

```text
out/bringup/qrzl903-01/android-restore-20260606/qrzl903-01-android-stock-preserve-nv-20260606.bin
```

| 项目 | 值 |
| --- | --- |
| SHA-256 | `37e4c70cdfc488c08fff204c4f010bbcc1f20e6977088253125aef2e8ca21339` |
| 大小 | `3867148288` bytes |
| Base image | `QRZL903-02` 原厂 Android 整盘备份 |
| 注入分区 | `QRZL903-01` 的 `modemst1`、`modemst2`、`fsc`、`fsg` |
| 写入方式 | EDL `wf` 整盘写入 |

恢复后读回验证：

```text
out/bringup/qrzl903-01/android-restore-20260606/readback/
```

| 分区 | SHA-256 |
| --- | --- |
| `boot` | `f22c615838e6056d97dad3a600e5f456d1206ff3381b6e9a75d2f3e4afbfc005` |
| `modemst1` | `7756161aa748787cfdbdea43a6c4db053339c013e680a3e2f13e774ffb902714` |
| `modemst2` | `1328f56b467703ee2a722e5597092cdb9f7100537823d37f189c6c59977576d4` |
| `fsc` | `648e09484cd8e9d20c8d30da365d687ccd26e174e2f64de48e271d60b0da6814` |
| `fsg` | `99f3cb09fffc74abd924b849116e7a2e977600c6502d1f2b1d5f289a47f7a70e` |

恢复后 Android 证据：

```text
out/bringup/qrzl903-01/android-restore-20260606/postboot/
```

已确认属性：

- `ro.serialno`: `a33fbfc`
- `gsm.version.baseband`: `UFI001CT 20211106`
- `ro.build.cust_proj`: `UFI001C`
- `ro.build.model_type`: `ZX_UFI001C`
- `ro.build.sw.custom.version`: `UFI_XG_WFSER_HW03CTDD_220615`
- `ro.build.date`: `2022年 06月 15日 星期三 15:51:53 CST`
- `persist.wlan.imei.fromnv`: `000000041775022`
- `persist.wlan.mac.fromnv`: `5c:a0:00:3c:a7:85`
- `service.adb.tcp.port`: `5555`
- `sys.usb.config`: `rndis,serial_smd,adb`

## QRZL903-02 原厂基准

样本 02 原厂 Android 整盘备份：

```text
out/bringup/qrzl903-02/edl-20260606/full-emmc-stock-android-20260606.bin
```

| 项目 | 值 |
| --- | --- |
| SHA-256 | `9c59c8a296f0f7d4d0923756d9f078b0176f06f497cf694b1ce4f13eb78fe2a5` |
| 大小 | `3867148288` bytes |
| Android build | `msm8916_32_512-userdebug 4.4.4 KTU84P eng.libinglin.20220615 test-keys` |
| Custom version | `UFI_XG_WFSER_HW03CTDD_220615` |
| Baseband | `UFI001CT 20211106` |

ADB 证据目录：

```text
out/bringup/qrzl903-02/adb-20260606-135442/
```

运行态设备树摘要：

```text
out/bringup/qrzl903-02/device-tree-20260606/qrzl903-02-runtime-device-tree-summary.json
```

运行态设备树：

| 字段 | 值 |
| --- | --- |
| `model` | `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` |
| `compatible` | `qcom,msm8916-mtp`, `qcom,msm8916`, `qcom,mtp` |
| `qcom,board-id` | `<8 0x100>` |
| `memory/reg` | `0x80000000` 起始，`0x20000000` 大小 |
| panel bootargs | `qcom,mdss_spi_st7735s_128128_cmd` |

## 已知外部包

```text
D:/123pan/Downloads/MIKO-QRZL903-1.zip
out/firmware-packages/miko-full-images/MIKO-QRZL903-1/QRZL903-1.bin
```

| 项目 | 值 |
| --- | --- |
| ZIP SHA-256 | `b2f23bb42db3a777c604666e8ecd2269d2447f35284534cc959cd91845caf1d6` |
| BIN SHA-256 | `8fb0b9b078ab646d5ffbf97abdaadac76f2743fce0329352c6cab8b592442fda` |
| BIN 大小 | `3875520000` bytes |
| 和实机差异 | 比 `QRZL903-01/02` eMMC 大 `8371712` bytes |
| Build | `eng.zengrongrong.20211124` |

该包和样本 02 分区起点一致，但版本更旧且尾部尺寸不适合整盘直写。

## 后续注意

- 恢复第三台或新样本时，优先读取 EDL serial、eMMC 大小和 GPT。
- 如果目标机器仍能读取自身 `modemst1/2`、`fsg/fsc`，恢复 Android 时应注入目标机器自己的备份。
- 如果目标机器身份分区损坏，不要直接使用 01 或 02 的身份分区，应先单独讨论 QCN/NV 恢复策略。
- 标准 Linux 方向仍优先验证上游 `thwc,ufi001c`，但物理板号继续按 `QRZL903-1` 单独记录。
