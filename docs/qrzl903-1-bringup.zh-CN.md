# QRZL903-1 bring-up 记录

本文记录 2026-06-06 两台 `QRZL903-1` 样本的只读检查、备份和设备树提取结果。

当前结论：

- 样本 01 曾被刷成 Linux/OpenWrt 风格 GPT；已保留原状态备份，并于 2026-06-06 恢复到 Android/MTP GPT。
- 样本 02 是本项目持有的原厂 Android/MIKO 类布局样本，已经完成 EDL 整盘只读备份。
- `MIKO-QRZL903-1.zip` 与样本 02 分区起点一致，但下载包最后 `userdata` 比实机大 8MiB，且系统版本更旧；恢复本项目 903 设备时，应优先参考样本 02 备份。

## 样本 01

| 项目 | 值 |
| --- | --- |
| 板型 | `QRZL903-1` |
| EDL USB | `05c6:9008` |
| EDL serial | `0x017a302b` |
| SoC | `MSM8916` |
| 当前 eMMC 大小 | `3867148288` bytes (`0xE6800000`) |
| 当前 GPT | Linux/OpenWrt 风格：`cdt`、`sbl1`、`rpm`、`tz`、`hyp`、`sec`、`modemst1/2`、`fsc`、`fsg`、`aboot`、`boot`、`devinfo`、`rootfs` |

EDL 分区表日志：

```text
out/bringup/qrzl903-01/edl-20260606/printgpt.txt
```

## 已备份

分区备份目录：

```text
out/bringup/qrzl903-01/edl-20260606/partitions/
```

已备份 `cdt`、`sbl1`、`rpm`、`tz`、`hyp`、`sec`、`modemst1`、`modemst2`、`fsc`、`fsg`、`aboot`、`boot`、`devinfo`、`rootfs`，并保存分区哈希：

```text
out/bringup/qrzl903-01/edl-20260606/partition-sha256.txt
```

关键哈希：

| 文件 | SHA-256 |
| --- | --- |
| `boot.bin` | `62760820fdec0bb42ed2f8364ae94ec16b6fc1b74c59e0906b7f90b8f04f4770` |
| `rootfs.bin` | `f985cf214dbd7e25fa595692854400627e4a5d7a4094b6533780224ea5dcfbf7` |
| `modemst1.bin` | `43cf140de89768785c26f57af4e216d7c43812eef778698ec4cd41fef9fbf785` |
| `modemst2.bin` | `c0fbfb2b40099f3b46a143485ab3d4b29ddacae85444d3994ad53ba7da11e12a` |
| `fsg.bin` | `703676e69645f597702fe8d5b114f1bc7303e5c66b620c545ac6669396c59237` |

## 样本 01 Android 恢复

2026-06-06 使用样本 02 原厂 Android 整盘备份作为底子，为样本 01 生成专用恢复镜像，并注入样本 01 已备份的 `modemst1`、`modemst2`、`fsc`、`fsg`。

恢复镜像：

```text
out/bringup/qrzl903-01/android-restore-20260606/qrzl903-01-android-stock-preserve-nv-20260606.bin
```

| 项目 | 值 |
| --- | --- |
| 恢复镜像 SHA-256 | `37e4c70cdfc488c08fff204c4f010bbcc1f20e6977088253125aef2e8ca21339` |
| 大小 | `3867148288` bytes |
| Base image | 样本 02 `full-emmc-stock-android-20260606.bin` |
| 注入分区 | `modemst1`、`modemst2`、`fsc`、`fsg` |
| 写入方式 | EDL `wf` 整盘写入 |

恢复 manifest：

```text
out/bringup/qrzl903-01/android-restore-20260606/qrzl903-01-android-restore-manifest.json
```

EDL 写入后读回验证：

```text
out/bringup/qrzl903-01/android-restore-20260606/readback/
```

读回哈希：

| 分区 | SHA-256 |
| --- | --- |
| `boot` | `f22c615838e6056d97dad3a600e5f456d1206ff3381b6e9a75d2f3e4afbfc005` |
| `modemst1` | `7756161aa748787cfdbdea43a6c4db053339c013e680a3e2f13e774ffb902714` |
| `modemst2` | `1328f56b467703ee2a722e5597092cdb9f7100537823d37f189c6c59977576d4` |
| `fsc` | `648e09484cd8e9d20c8d30da365d687ccd26e174e2f64de48e271d60b0da6814` |
| `fsg` | `99f3cb09fffc74abd924b849116e7a2e977600c6502d1f2b1d5f289a47f7a70e` |

恢复后 Android 验证：

| 项目 | 值 |
| --- | --- |
| ADB serial | `a33fbfc` |
| Build | `UFI_XG_WFSER_HW03CTDD_220615` |
| Baseband | `UFI001CT 20211106` |
| RIL IMEI | `864405028082598` |
| NV Wi-Fi MAC | `5c:a0:00:3c:a7:85` |
| Android GPT | 已恢复为 `modem`、`sbl1`、`aboot`、`boot`、`system`、`persist`、`cache`、`recovery`、`userdata` 等 |
| USB/network | `192.168.100.1:80` 和 `192.168.100.1:5555` 可连接 |

Post-boot 证据：

```text
out/bringup/qrzl903-01/android-restore-20260606/postboot/
```

## 样本 02

| 项目 | 值 |
| --- | --- |
| 板型 | `QRZL903-1` |
| ADB serial | `d0b1d17` |
| EDL serial | `0x0b723827` |
| SoC | `MSM8916` |
| eMMC 大小 | `3867148288` bytes (`0xE6800000`) |
| GPT | Android/MTP 风格：`modem`、`sbl1`、`aboot`、`boot`、`system`、`persist`、`cache`、`recovery`、`userdata` 等 |
| Android build | `msm8916_32_512-userdebug 4.4.4 KTU84P eng.libinglin.20220615 test-keys` |
| Baseband | `UFI001CT 20211106` |
| Custom version | `UFI_XG_WFSER_HW03CTDD_220615` |
| Model type | `ZX_UFI001C` |
| RIL IMEI | `861386074067431` |
| NV Wi-Fi MAC | `5c:a0:00:3c:80:2c` |

ADB 证据目录：

```text
out/bringup/qrzl903-02/adb-20260606-135442/
```

EDL 整盘备份：

```text
out/bringup/qrzl903-02/edl-20260606/full-emmc-stock-android-20260606.bin
```

| 文件 | SHA-256 | 大小 |
| --- | --- | ---: |
| `full-emmc-stock-android-20260606.bin` | `9c59c8a296f0f7d4d0923756d9f078b0176f06f497cf694b1ce4f13eb78fe2a5` | `3867148288` bytes |
| `proc-device-tree.zip` | `0f0147c0dca0a6cd2ec35ee9d709c67f67a322a4a4d364f6765538c2c5917fb0` | - |

样本 02 运行态设备树：

| 字段 | 值 |
| --- | --- |
| `model` | `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` |
| `compatible` | `qcom,msm8916-mtp`, `qcom,msm8916`, `qcom,mtp` |
| `qcom,board-id` | `<8 0x100>` |
| `memory/reg` | `0x80000000` 起始，`0x20000000` 大小 |
| panel bootargs | `qcom,mdss_spi_st7735s_128128_cmd` |

运行态设备树摘要：

```text
out/bringup/qrzl903-02/device-tree-20260606/qrzl903-02-runtime-device-tree-summary.json
```

样本 02 `boot.img` 中的 QCDT/FDT 已提取：

```text
out/bringup/qrzl903-02/device-tree-20260606/qrzl903-02-boot-fdt-summary.json
```

样本 02 的分区起点与 `MIKO-QRZL903-1.bin` 一致，最后 `userdata` 为 `2623995392` bytes，正好比下载包小 `8388608` bytes。

已切出的可对比分区哈希：

```text
out/bringup/qrzl903-02/edl-20260606/split-selected/partition-sha256.txt
```

与 `MIKO-QRZL903-1.bin` 的关键差异：

| 分区 | 是否相同 | 说明 |
| --- | --- | --- |
| `modem`、`sbl1/sbl1bak`、`rpm/rpmbak`、`tz/tzbak`、`hyp/hypbak`、`misc`、`splash`、`DDR`、`sec` | 相同 | 底层固件主体同源 |
| `aboot/abootbak` | 不同 | 样本 02 为 2022-06-15 版本 |
| `boot`、`system`、`recovery` | 不同 | 样本 02 系统版本更新 |
| `userdata` | 尺寸不同 | 样本 02 适配 `0xE6800000` eMMC，下载包尾部大 8MiB |

## 当前 boot 设备树

当前 `boot.bin` 是 Android boot image 格式，但包含 `OpenWrt` 标记，并内嵌一个标准 FDT。

提取产物：

```text
out/bringup/qrzl903-01/device-tree-20260606/qrzl903-01-current-boot.dtb
out/bringup/qrzl903-01/device-tree-20260606/qrzl903-01-current-boot.dts
```

哈希：

| 文件 | SHA-256 |
| --- | --- |
| `qrzl903-01-current-boot.dtb` | `f140983483b78a99f60071ed34ceddab960e3ae9791076ad2395cd11bf2fa5de` |
| `qrzl903-01-current-boot.dts` | `0bc5cf53af74cea435b684c119845d1641c668c9b5714b8891bfe1951e95c73e` |

设备树根节点：

| 字段 | 值 |
| --- | --- |
| `model` | `ufi-001c 4G Modem Stick` |
| `compatible` | `thwc,ufi001c`, `qcom,msm8916` |

这和 lk2nd 上游 `msm8916-512mb-mtp.dts` 中的 `thwc,ufi001c` 节点方向一致。实物仍应按 `QRZL903-1` 单独记录，因为板号和分区布局是实机证据。

## MIKO-QRZL903-1 包

已知下载包：

```text
D:/123pan/Downloads/MIKO-QRZL903-1.zip
```

包内全盘镜像：

```text
out/firmware-packages/miko-full-images/MIKO-QRZL903-1/QRZL903-1.bin
```

| 项目 | 值 |
| --- | --- |
| ZIP SHA-256 | `b2f23bb42db3a777c604666e8ecd2269d2447f35284534cc959cd91845caf1d6` |
| BIN SHA-256 | `8fb0b9b078ab646d5ffbf97abdaadac76f2743fce0329352c6cab8b592442fda` |
| BIN 大小 | `3875520000` bytes |
| 比样本 01/02 eMMC 大 | `8371712` bytes |
| BIN GPT | Android/MTP 风格：`modem`、`sbl1`、`aboot`、`boot`、`system`、`persist`、`cache`、`recovery`、`userdata` 等 |
| 标记 | `UFI001CT 20211106`、`UFI001C`、`msm8916_32_512` |
| Build | `eng.zengrongrong.20211124` |

包内 `boot.img` 已切出并解析 QCDT：

```text
out/firmware-packages/miko-full-images/MIKO-QRZL903-1/qcdt-from-boot/qcdt-paired-summary.json
```

其中 `platform_id=206`、`variant_id=8`、`subtype_id=256` 的 DTB SHA-256 为：

```text
7d4a2b2044c7073d27b5af7162fff83750e24475ca095e08d1b0557632f0fb7f
```

该哈希与此前 UFI003_MB_V02 的 Android MTP DTB 完全相同，说明 Android/MIKO 运行态仍是通用 MTP 设备树。它能作为原厂 Android 布局证据，但不能单独证明 QRZL903-1 在标准 Linux 下需要新增独立 DTS。

## 当前判断

- 不应整盘写下载的 `QRZL903-1.bin`：镜像大于两台样本 eMMC。
- 样本 01 的 OpenWrt/Linux GPT 已作为历史状态备份；恢复 Android 时不应直接按旧 Linux 分区名刷写下载包。
- 样本 02 已提供本项目自己的原厂 Android 整盘备份，恢复 903 时应优先使用它的 GPT/分区大小作为基准。
- 恢复其他 903 个体时，仍必须保护每台自己的 `modemst1`、`modemst2`、`fsg`、`fsc`、`persist`、`userdata` 等身份、校准和持久化数据。

## 下一步

1. 保留样本 02 作为原厂 Android/MTP 基线，不作为首轮标准 Linux 写入对象。
2. 使用已恢复 Android 的样本 01 先验证上游 `thwc,ufi001c` lk1st/lk2nd 选择是否正确。
3. 在编译机重新构建 `lk2nd-msm8916.img` 与 `thwc-ufi001c-lk1st-msm8916.mbn`，记录 SHA-256、构建日期和源码版本。
4. 首轮刷写只碰启动链相关分区；每次写入前重新确认并备份该机 `modemst1`、`modemst2`、`fsg`、`fsc`、`persist`、`userdata` 等身份、校准和持久化数据。
5. 刷写结果回写到 `docs/qrzl903-device-inventory.zh-CN.md`、`docs/device-matrix.md` 和 `devices/openstick/qrzl903-1.yaml`。
