# thwc-ufi001c 真机验证报告

验证时间：2026-10-18 05:30 ~ 05:37 (GMT+8)
验证方式：UART 串口 (CH340 / COM5 / 115200 8N1) + serial getty 登录

## 结论

**设备已完整启动 postmarketOS edge，4G 上网正常，USB 网络共享工作，WiFi 驱动栈完整可用，零失败服务。**

此前"未验证启动"的判断不成立 —— 设备实际早已跑通全链路。
`wlan0 DOWN` 也已查清：不是故障，是从未配置过 WiFi 连接。

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

## WiFi 验证（wcn36xx）

`ip -br addr` 里 `wlan0 DOWN` 曾被误读为"WiFi 不可用"。实测结果是**硬件与驱动完全正常，只是从未配置过任何连接**。

### 固件与驱动加载链（`journalctl -k`）

```
remoteproc remoteproc0: Booting fw image wcnss.mdt, size 7260
qcom_wcnss_ctrl remoteproc0:smd-edge.WCNSS_CTRL.-1.-1: WCNSS Version 1.5 1.2
wcn36xx: mac address: 02:00:26:e0:0:41:bc
qcom-wcnss-pil a204000.remoteproc: unexpected response to sysmon event
wcn36xx: firmware WLAN version 'WCN V2.0 RadioPhy vUnknown with 19.2MHz XO' and CRM version '00110'
wcn36xx: firmware API 1.5.1.2, 411 stations, 2 bssids
```

- WCNSS remoteproc 正常 boot，`wcnss.mdt` 固件下载成功
- `wcn36xx` 拿到固件 API 1.5.1.2，411 station / 2 bssid —— 完整可用
- `unexpected response to sysmon event` 是 MSM8916 上的已知良性告警，不影响功能

### 射频与扫描

```
$ rfkill list
0: phy0: Wireless LAN
        Soft blocked: no
        Hard blocked: no

$ nmcli dev wifi rescan        # 需 root，普通用户被 polkit 拒绝
$ nmcli -f SSID,SIGNAL,SECURITY dev wifi list
SSID           SIGNAL  SECURITY
ChinaNet-2feQ  94      WPA1 WPA2
Kumquat_2.4G   75      WPA2 WPA3
qiuqiu         70      WPA1 WPA2
LIN-1          54      WPA1 WPA2
CU_kwXd        54      WPA1 WPA2
...            (共 18 个 AP)
```

**扫描正常返回 18 个真实 AP**，说明射频、天线、固件、驱动全链路工作。

### 接口状态解读

```
$ ip link show wlan0
3: wlan0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue
   state DOWN mode DORMANT
   link/ether 5e:5e:a1:ce:38:46 brd ff:ff:ff:ff:ff:ff
   permaddr 02:00:26:e0:41:bc
```

- `permaddr` 与内核日志中 wcn36xx 的 MAC 一致，驱动 MAC 已正确注入
- `link/ether` 是 NetworkManager 的 MAC 随机化结果（默认行为）
- `NO-CARRIER / DOWN / DORMANT` 是**未关联 AP 的 station 接口标准状态**，不是故障

### 为什么没连上

```
$ nmcli -t -f NAME,TYPE,AUTOCONNECT con show
wwan0qmi0:gsm:yes
lo:loopback:yes
```

NetworkManager 里**只有 4G 和 lo 两个连接，从未存在任何 WiFi 连接配置**。`wlan0` 显示 `wifi:disconnected`（而非 `unavailable`），正是"设备就绪、等待配置"的状态。

**结论：WiFi 无功能缺口。** 剩下的只是"没有 SSID/密码"，属于配置问题而非移植问题。

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
3. ~~`wlan0` 处于 DOWN —— WiFi 未启用~~
   **已排除**：WiFi 硬件/固件/驱动/射频全部正常，扫描可返回 18 个 AP。
   `wlan0` DOWN 仅因为从未配置过 WiFi 连接（见上文「WiFi 验证」）。
   待办只剩一项：填入实际 SSID/密码做一次关联测试。

## 复现方式

推荐用 `tools/serial_console.ps1`，一次开关端口跑完一批命令（getty 在端口反复开关时会丢登录态）：

```powershell
# 命令文件：一行一条，UTF-8
$sb = [scriptblock]::Create((Get-Content -Raw tools/serial_console.ps1))
& $sb -Port COM5 -CmdFile out/cmds.txt
```

脚本会自动做三件容易踩坑的事：

1. **脱困分页器** —— 先发 `q` / Ctrl-C，避免上一轮卡在 `less` 里吞掉所有按键
2. **单次开关端口** —— 登录态不丢
3. **剥 ANSI 转义** —— 输出可读

手工登录：

```
串口: COM5 @ 115200 8N1 (CH340, VID_1A86 PID_7523)
用户: pmos / 密码: pmos
```

### 两个已踩过的坑

**① `sudo` 在串口上密码认证会失败。** 不是密码错、也不是用户不在 wheel（`pmos` 确实在 `10(wheel)`），
而是 tty 上的密码输入时序被回显打乱。绕过方式：

```sh
echo pmos | sudo -S -p '' id
# uid=0(root) gid=0(root) ...
```

**② 所有命令都加 `| cat`。** `nmcli` / `journalctl` 在 tty 上会自动走 `less`，
一旦卡进去，后续命令会被当成 pager 按键（表现为 `Pattern not found: ...`）。
`export PAGER=cat SYSTEMD_PAGER=cat` 有效，但管道到 `cat` 更保险。

**③ `nmcli dev wifi rescan` 需要 root。** 普通用户会拿到
`Error: ...wifi.scan request failed: not authorized.`（polkit 不放行串口会话）。
`nmcli dev wifi list` 只读缓存，不需要 root。

