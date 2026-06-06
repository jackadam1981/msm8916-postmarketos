# UFI003 设备清单

本文用于记录多台 `UFI003_MB_V02` 设备的可区分信息和刷机状态，避免三台机器的身份分区、备份和固件状态混淆。

## 记录原则

- 每台机器刷机前先备份 `modemst1`、`modemst2`、`fsg`、`fsc`、`ssd`、`persist`，条件允许时再备份整盘 eMMC。
- 刷回原厂/MIKO 固件时，优先只写 `aboot`、`abootbak`、`boot`、`recovery`、`system`。
- 不要把一台机器的 `modemst1/2`、`fsg/fsc`、`persist`、`ssd`、`userdata` 写到另一台机器上。
- `IMEI(RIL)` 以 Android `dumpsys iphonesubinfo` 返回的 `Device ID` 为准；`persist.wlan.imei.fromnv` 作为厂商属性记录。
- 机身贴纸信息如果由人工确认，记录在“贴纸/外观信息”栏；不要用照片猜测结果覆盖系统实际读数。

## 设备列表

| 编号 | PCB | 当前固件 | ADB/USB 序列号 | IMEI(RIL) | 厂商 NV IMEI | Wi-Fi MAC(NV) | RNDIS MAC | Wi-Fi SSID | 贴纸/外观信息 | 备份位置 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UFI003-01 | `UFI003_MB_V02` | MIKO/YunKeMao `UFI_YKM_HW01CTDE_V040_220507` | `1db15d2` | `861048063913393` | `000000041775022` | `5c:a0:00:3d:fa:35` | `ea:ea:19:70:a3:4b` | `4G-UFI-` | 待人工确认贴纸 SN/IMEI | `out/bringup/410-android/edl-20260606/` | 已由错误包刷回 3.53G MIKO UFI003；TCP ADB 为 `192.168.100.1:10242` |
| UFI003-02 | `UFI003_MB_V02` | MIKO/YunKeMao `UFI_YKM_HW01CTDE_V040_220507` | `26e041bc` | `866241028178104` | `000000041775022` | `5c:a0:00:73:6d:11` | `4e:11:1a:41:09:8c` | 待读取 | 待人工确认 | `out/bringup/ufi003-02/edl-20260606/` | eMMC `3791650816` 字节/`3.5312 GiB`，EDL serial `0x2106918a`；已刷回 3.53G MIKO UFI003，身份分区未写入 |
| UFI003-03 | `UFI003_MB_V02` | MIKO/YunKeMao `UFI_YKM_HW01CTDE_V040_220507` | `216ffcc1` | `866241019366411` | `000000041775022` | `5c:a0:00:54:bb:18` | `02:41:46:6f:a7:e9` | 待读取 | 待人工确认 | `out/bringup/ufi003-03/edl-20260606/` | eMMC `3791650816` 字节/`3.5312 GiB`，EDL serial `0x02bcdd15`；已刷回 3.53G MIKO UFI003，身份分区未写入 |

## UFI003-01 已确认信息

- `gsm.version.baseband`: `UFI003_CT 20211210`
- `ro.build.cust_proj`: `YunKeMao`
- `ro.build.sw.custom.version`: `UFI_YKM_HW01CTDE_V040_220507`
- `ro.build.hw.version`: `HW1.3`
- `ro.build.description`: `msm8916_32_512-userdebug 4.4.4 KTU84P eng.liufeihua.20220507 test-keys`
- `persist.cpe.gw.ip`: `192.168.100.1`
- `service.adb.tcp.port`: `10242`
- `persist.adb.tcp.port`: `10242`
- `sys.usb.config`: `rndis,serial_smd,adb`

## UFI003-01 备份

- EDL 整盘备份: `out/bringup/410-android/edl-20260606/full-emmc-before-miko353.bin`
- 整盘大小: `3791650816`
- 整盘 SHA256: `71E18FC2F9CCE42E9E9BFF2F05944E7A6B1E37E6EA9FE3E528709BC85BCA1DAF`
- EDL 分区备份: `out/bringup/410-android/edl-20260606/partitions/`
- 写入后校验目录: `out/bringup/410-android/edl-20260606/after-miko353-verify/`

## UFI003-02 EDL 信息

- EDL serial: `0x2106918a`
- HWID: `0x007050e100000000`
- CPU: `MSM8916`
- PK_HASH: `0xcc3153a80293939b90d02d3bf8b23e0292e452fef662c74998421adad42a380f`
- GPT 总大小: `0x00000000e2000000` 字节，`0x0000000000710000` 个 512 字节扇区
- 折算容量: `3791650816` 字节，约 `3.7917 GB` / `3.5312 GiB`

## UFI003-02 已确认信息

- `ro.serialno`: `26e041bc`
- `ro.boot.serialno`: `26e041bc`
- `gsm.version.baseband`: `UFI003_CT 20211210`
- `ro.build.cust_proj`: `YunKeMao`
- `ro.build.sw.custom.version`: `UFI_YKM_HW01CTDE_V040_220507`
- `ro.build.hw.version`: `HW1.3`
- `ro.build.description`: `msm8916_32_512-userdebug 4.4.4 KTU84P eng.liufeihua.20220507 test-keys`
- `persist.cpe.gw.ip`: `192.168.100.1`
- `service.adb.tcp.port`: `10242`
- `persist.adb.tcp.port`: `10242`
- `sys.usb.config`: `rndis,serial_smd,adb`

## UFI003-02 备份

- EDL 整盘备份: `out/bringup/ufi003-02/edl-20260606/full-emmc-before-miko353.bin`
- 整盘大小: `3791650816`
- 整盘 SHA256: `4BC310DF01AE6F6966CFF8230101C6AD414CB84CD1B0FE05666B9F61FC7F98C2`
- EDL 分区备份: `out/bringup/ufi003-02/edl-20260606/partitions/`
- 写入后校验目录: `out/bringup/ufi003-02/edl-20260606/after-miko353-verify/`
- 已确认读回匹配: `aboot`、`abootbak`、`boot`、`recovery`
- `system` 读回在 Windows 控制台进度输出异常后中断，读回文件不完整，需重新枚举 9008 后再复核或开机验证。

## UFI003-03 EDL 信息

- EDL serial: `0x02bcdd15`
- HWID: `0x007050e100000000`
- CPU: `MSM8916`
- PK_HASH: `0xcc3153a80293939b90d02d3bf8b23e0292e452fef662c74998421adad42a380f`
- GPT 总大小: `0x00000000e2000000` 字节，`0x0000000000710000` 个 512 字节扇区
- 折算容量: `3791650816` 字节，约 `3.7917 GB` / `3.5312 GiB`

## UFI003-03 已确认信息

- `ro.serialno`: `216ffcc1`
- `ro.boot.serialno`: `216ffcc1`
- `gsm.version.baseband`: `UFI003_CT 20211210`
- `ro.build.cust_proj`: `YunKeMao`
- `ro.build.sw.custom.version`: `UFI_YKM_HW01CTDE_V040_220507`
- `ro.build.hw.version`: `HW1.3`
- `ro.build.description`: `msm8916_32_512-userdebug 4.4.4 KTU84P eng.liufeihua.20220507 test-keys`
- `persist.cpe.gw.ip`: `192.168.100.1`
- `service.adb.tcp.port`: `10242`
- `persist.adb.tcp.port`: `10242`
- `sys.usb.config`: `rndis,serial_smd,adb`
- `persist.sys.usb.config`: `diag,serial_smd,rmnet_bam,adb`

## UFI003-03 备份

- EDL 分区备份: `out/bringup/ufi003-03/edl-20260606/partitions/`
- EDL 按分区展开备份: `out/bringup/ufi003-03/edl-20260606/full-emmc-before-miko353.bin/`
- 分区 SHA256: `out/bringup/ufi003-03/edl-20260606/partition-sha256.txt`
- 写入记录: `out/bringup/ufi003-03/edl-20260606/miko353-write.done.txt`
