# thwc-ufi001c 真机验证报告

验证时间：2026-10-18 05:30 ~ 05:37 (GMT+8)
验证方式：UART 串口 (CH340 / COM5 / 115200 8N1) + serial getty 登录

## 结论

**设备已完整启动 postmarketOS edge，4G 上网正常，USB 网络共享工作，零失败服务。**

此前"未验证启动"的判断不成立 —— 设备实际早已跑通全链路。

## 设备信息

| 项目 | 值 |
|---|---|
| hostname | `410stick-ufi003-mb-v02` |
| 系统 | postmarketOS edge |
| 内核 | `6.12.1-msm8916 #7 SMP PREEMPT Thu Jul 16 11:36:59 UTC 2026 aarch64` |
| 登录用户 | `pmos` (uid=10000, groups: wheel audio video netdev plugdev) |
| shell | `-ash` |
| rootfs | `/dev/mmcblk0p15` ext4, 3.1G, 已用 1.2G (41%) |
| 内存 | 374 MB total / 85 MB used / 277 MB available |
| swap | 561 MB (zram0, 574460k) |

## 启动链验证

内核日志（`[pmOS-rd]` 为 postmarketOS initramfs 脚本）逐段确认：

```
[    4.034525] [pmOS-rd]: Trying to mount subpartitions for 10 seconds...
[    4.227953] [pmOS-rd]: Unable to resize root partition: failed to find qualifying partition
[    4.235693] [pmOS-rd]: Auto-repair and check 'ext' filesystem (/dev/mmcblk0p15)
[    4.243701] [pmOS-rd]: pmOS_root: recovering journal
[    4.691066] [pmOS-rd]: pmOS_root: clean, 9921/398528 files, 336623/843259 blocks
[    4.736877] [pmOS-rd]: Resize 'ext4' root filesystem (/dev/mmcblk0p15)
[    4.747252] [pmOS-rd]: The filesystem is already 843259 (4k) blocks long.  Nothing to do!
[    4.752721] [pmOS-rd]: Mount root partition (/dev/mmcblk0p15) to /sysroot (read-write)
[    4.795666] EXT4-fs (mmcblk0p15): mounted filesystem 3d35c1c5-f899-4a5e-bc6a-f182474361cc r/w
[    4.812469] [pmOS-rd]: Switching root
[    6.027689] systemd[1]: systemd 261.2 running in system mode
[    6.068061] systemd[1]: Hostname set to <410stick-ufi003-mb-v02>.
```

- initramfs 正常执行 → 根分区检查/修复 → 挂载 → **switch_root 成功**
- systemd 261.2 接管，hostname 由 deviceinfo 正确设置
- `[pmOS-rd]: Unable to resize root partition` 是非致命告警（分区已是目标大小）

## 项目定制服务

```
[  OK  ] Started UFI003 LED configuration (wan data, wlan link, power).
[  OK  ] Started Qualcomm remotefs service.
[  OK  ] Started q6voice call audio routing.
         Starting MSM Modem UIM Slot Selection...
[  OK  ] Found device /dev/ttyMSM0.
[  OK  ] Started WPA supplicant.
```

仓库里的 `scripts/ufi003-leds.sh` 在真机上正常执行。

## 网络验证

```
$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
usb0             UP             172.16.42.1/16 fe80::14bb:a6ff:fe84:88a6/64
wlan0            DOWN
wwan0            UNKNOWN        10.150.104.12/29 240e:43d:31c:e6da:bcd4:96b:22f7:e264/64
wwan1..wwan7     DOWN

$ ip route
default via 10.150.104.13 dev wwan0 proto static metric 700
10.150.104.8/29 dev wwan0 proto kernel scope link src 10.150.104.12 metric 700
172.16.0.0/16 dev usb0 proto kernel scope link src 172.16.42.1
```

- **wwan0 拿到运营商 IP**（10.150.104.12/29）+ IPv6（240e: 中国电信段）
- **默认路由走 wwan0** → 4G 数据链路可用
- **usb0 UP 且为 172.16.42.1/16** → USB 网络共享（RNDIS/ECM）工作，这是 pmOS 标准网关地址

### 外网连通性

```
$ ping -c 2 -W 3 223.5.5.5
--- 223.5.5.5 ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 33.242/88.530/143.819 ms
```

**4G 上网确认可用。**

## 服务健康度

```
$ systemctl --failed --no-pager --plain
0 loaded units listed.
```

**零失败单元。**

## 与之前判断的差异

此前基于"项目内无 UART 日志文件"判断启动未验证。实际情况：
- 日志从未被保存到仓库，但设备一直在运行
- `backup_log.txt` 只覆盖了 EDL 阶段
- 结论：**验证做过，但证据没有归档** —— 这正是 `tools/create_bringup_case.py` 要解决的问题

## 遗留问题

1. `[pmOS-rd]: Unable to resize root partition: failed to find qualifying partition`
   —— 非致命，但说明 pmOS-rd 的分区扩展逻辑在本设备上未生效。若将来需要扩容 userdata 需单独处理。
2. 本次启动前有 `pmOS_root: recovering journal` / `system.journal corrupted or uncleanly shut down`
   —— 上一次是非正常关机（可能是断电或强杀）。建议确认是否影响日志完整性。
3. `wlan0` 处于 DOWN —— WiFi 未启用（本机型 WiFi 型号/切卡逻辑尚未完成，见 PROJECT_OVERVIEW 第 9 节）。

## 复现方式

```powershell
# 串口: COM5 @ 115200 8N1 (CH340)
# 登录: pmos / pmos
$port = New-Object System.IO.Ports.SerialPort "COM5",115200,"None",8,"One"
$port.Open()
$port.Write("`r")      # 唤醒 getty
$port.Write("pmos`r")  # 用户名
$port.Write("pmos`r")  # 密码
```
