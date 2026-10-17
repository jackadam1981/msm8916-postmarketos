# Notes

## 硬件

- 板号：thwc-ufi001c（设备代号 `410stick-ufi003-mb-v02`），SoC MSM8916 (Snapdragon 410)
- 存储：eMMC；rootfs 位于 `/dev/mmcblk0p15`，ext4，3.1 GB（已用 1.2 GB / 41%）
- 内存：374 MB 可用（实测 `free -h` total 374.0M），zram0 swap 561 MB
- Wi-Fi/BT：`wlan0` 存在但处于 DOWN —— WiFi 型号/切卡逻辑尚未完成
- SIM/TF：SIM 可用（`wwan0` 取得运营商地址 10.150.104.12/29 + IPv6 240e: 段）；TF 未验证
- 按键/测试点：未记录照片（待补 `photos/`）

## 启动模式

- 正常模式 USB ID：未采集（待补 `lsusb` 输出）
- fastboot USB ID：未采集
- EDL USB ID：`0x05c6:0x9008`（Qualcomm HS-USB QDLoader 9008），已验证可连接
  - firehose loader 实测可用：`Loaders/xiaomi/prog_emmc_firehose_8916_gucci_peek.mbn`

## 运行时实测（2026-10-18）

- 内核：`6.12.1-msm8916 #7 SMP PREEMPT Thu Jul 16 11:36:59 UTC 2026 aarch64`
- 系统：postmarketOS edge，systemd 261.2
- hostname：`410stick-ufi003-mb-v02`
- 登录：serial getty on `ttyMSM0` @115200，用户 `pmos`
- 失败服务：0
- 外网：ping 223.5.5.5 丢包 0%，RTT 33–143 ms
- USB 网络共享：`usb0` UP，172.16.42.1/16
- 4G：`wwan0` UP，默认路由 `via 10.150.104.13`

## 风险

- 未确认事项：
  - `wlan0` 为何 DOWN（缺固件 / 型号未识别 / 切卡逻辑未完成）
  - `[pmOS-rd]: Unable to resize root partition: failed to find qualifying partition`
    的原因 —— 非致命，但说明 pmOS-rd 扩容逻辑在本设备未生效
  - 上次关机为非正常关机（`pmOS_root: recovering journal`、`system.journal corrupted`）
- 不可刷写分区：`modem`、`persist`、`fsg`、`fsc` —— 已备份至 `backup/device-2026-07-31/`
- 恢复路径：EDL 刷回 `backup/device-2026-07-31/` 下的 `aboot.bin` / `boot.bin` /
  `gpt_main.bin` / `gpt_backup_*.bin`，NV 用 `modem`、`persist` 备份恢复
