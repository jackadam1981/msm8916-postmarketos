# RNDIS LAN（192.168.100.1）实现与验证

日期：2026-10-18
设备：`410stick-ufi003-mb-v02`（UFI003-02，MSM8916）
内核：`6.12.1-msm8916`，postmarketOS edge

---

## 1. 目标

| 项 | 要求 | 状态 |
|----|------|------|
| RNDIS 自动驱动 | Windows 插上即认，不装驱动 | ✅ |
| LAN 地址 | `192.168.100.1` | ✅ |
| DHCP | 主机自动拿地址 | ✅ 租约 `192.168.100.95` |
| SSH 管理 | 通过 LAN 登录 | ✅ `SSH_AUTH_OK` |
| NAT 出网 | 主机经 4G 上网 | ✅ ping 32-34 ms，HTTP 200 |
| 多机不冲突 | 同款棒子插同一主机 MAC 不撞 | ✅ 按序列号派生（4.1） |
| NV 可读 | `/persist` 挂载 | ✅ 只读（4.2） |

TTL 管理不属于本期目标（仅作为开发期诊断手段），见第 7 节。

---

## 2. 根因：参数确实是错的

设备上读到的 gadget 属性：

```
/sys/kernel/config/usb_gadget/g1/functions/rndis.usb0/class    = 02
/sys/kernel/config/usb_gadget/g1/functions/rndis.usb0/subclass = 06
/sys/kernel/config/usb_gadget/g1/functions/rndis.usb0/protocol = 00
```

`02/06/00` 是 **CDC-ECM** 的三元组，不是 RNDIS。Windows 侧对应表现：

```
Status  Class   FriendlyName        InstanceId
Error   RNDIS   (空)                USB\VID_05C6&PID_90B4&MI_00\...
ProblemCode : 28                     ← 没有可用驱动
CompatibleIds:
  USB\Class_02&SubClass_06&Prot_00
```

Windows 没有 CDC-ECM 的 inbox 驱动，所以只能停在 Code 28。

## 3. 为什么原版 Android 能自动驱动

Android 的 gadget 除了功能是 RNDIS 之外，还额外做两件事，缺一不可：

1. **接口三元组用 RNDIS 规范值 `E0/01/03`**（Wireless Controller / RF / RNDIS）
2. **发布 Microsoft OS 描述符**：
   - `os_desc/use=1`、`os_desc/b_vendor_code=0xcd`、`os_desc/qw_sign=MSFT100`
   - `functions/rndis.usb0/os_desc/interface.rndis/compatible_id=RNDIS`
   - `.../sub_compatible_id=5162001`

有了 OS 描述符，主机侧硬件 ID 会出现 `USB\MS_COMP_RNDIS`，Windows 据此自动加载 `usb8023.sys`（"Remote NDIS Compatible Device"），**不需要任何手动装驱动**。

原 gadget 的 `os_desc` 目录存在但全是默认值（`use=0`、`b_vendor_code=0x01`），等于没启用。

## 4. 修复

新增 `scripts/device/usb-lan.sh` + `scripts/device/usb-lan.service`，逻辑：

1. 拆掉 initramfs 留下的 `g1`
2. 重建 gadget：
   - `idVendor=0x05c6` / `idProduct=0x90b4`（保持原厂 VID/PID）
   - `bDeviceClass=0xEF/0x02/0x01`（复合设备，让 Windows 走 usbccgp 分到 MI_00）
   - `functions/rndis.usb0` 写 `class=0xE0`、`subclass=0x01`、`protocol=0x03`
   - 建 `os_desc` 三件套 + `compatible_id=RNDIS` + `sub_compatible_id=5162001`
   - MAC **按板级序列号派生**（见第 4.1 节），不再写死
   - USB `serialnumber` 也用序列号（`ufi003-26e041bc`），否则多台机器插同一主机
     会被识别成同一个 USB 设备
3. `usb0` 配 `192.168.100.1/24`（保留 `172.16.42.1/16` 作为 initramfs 恢复路径）
4. `dnsmasq` 只做 DHCP：`192.168.100.10-100`，网关 `.1`，DNS 下发 `223.5.5.5`/`114.114.114.114`
5. `nft` 加 `192.168.100.0/24 → wwan*` masquerade

> 注意：写完 `os_desc` 后，内核会把 `class/subclass/protocol` 读回成 `00/00/00`。
> 这是有意的——启用 OS 描述符后主机改用 `MS_COMP_RNDIS` 匹配，不再依赖接口类。
> 不要去"修"这个 00。

### 4.1 MAC 派生（多机不冲突）

UFI003 是一族同款板子，写死 MAC 会让第二台插上同一主机时冲突，而且症状很隐蔽
（第二台拿不到 DHCP）。改用板级序列号派生，规则和 `wcn36xx` 对 `wlan0` 用的完全一致：

```
序列号 26e041bc
        └── wlan0  02:00:26:e0:41:bc      ← 内核派生（基准）
            usb0   02:00:26:e0:41:be      ← base + 2
            host   02:00:26:e0:41:bf      ← base + 3
```

`+2/+3` 是为了避开 `wlan0`：两个接口同 MAC 会让主机的 ARP 表反复翻动。

实测三台（清单里的序列号）派生结果互不相同：

| 序列号 | usb0 (dev) | 主机 (host) |
|---|---|---|
| `26e041bc` | `02:00:26:e0:41:be` | `02:00:26:e0:41:bf` |
| `1db15d2`（左补零） | `02:00:01:db:15:d4` | `02:00:01:db:15:d5` |
| `216ffcc1` | `02:00:21:6f:fc:c3` | `02:00:21:6f:fc:c4` |

优先级：`/etc/usb-lan/mac.conf` 覆盖 → 序列号派生 → 内置兜底（并打 WARN）。

```sh
$ usb-lan.sh mac
[usb-lan] MAC from serial 26e041bc: dev=02:00:26:e0:41:be host=02:00:26:e0:41:bf
serial   : 26e041bc
dev_addr : 02:00:26:e0:41:be
host_addr: 02:00:26:e0:41:bf
```

> 为什么不用 NV 里的 MAC：查过了，这族没有。`/persist` 里只有
> `WCNSS_qcom_wlan_nv.bin`（2022-11-01 的通用校准模板，**全文件没有 `5ca0` OUI**）
> 和一个模板 `.bt_nv.bin`（BD_ADDR `e4:a8:10:00:00:08`，尾部像默认值）。
> `modemst1` / `modemst2` / `fsg` 里也搜不到清单记录的原厂 MAC。
> 序列号是这台机器上唯一稳定的个体标识，这也是 `wcn36xx` 退而用它派生的原因。

### 4.2 persist 分区挂载

**改之前 `/persist` 根本没挂载**，整个系统读不到任何 NV / 校准数据。这比 MAC 更根本：
没有 persist，WiFi 校准、BT 地址、传感器标定全都拿默认值。

新增 `scripts/device/persist.mount`：

```ini
[Mount]
What=/dev/disk/by-partlabel/persist
Where=/persist
Type=ext4
Options=ro,relatime
```

三个设计决定：

| 决定 | 原因 |
|---|---|
| 用 mount unit 而不是 `/etc/fstab` | fstab 是安装时生成的，设备包带不走；刷机后挂载会丢 |
| 用 `PARTLABEL` 而不是 `UUID` | 重刷 persist 文件系统会改 UUID，GPT 分区名不变 |
| `ro` + `ConditionPathExists` | 只读防误写（这是厂校准的唯一副本）；条件不满足时 unit 被跳过而不是失败，等价 `nofail` |

装法（设备包集成前手动）：

```sh
sudo cp persist.mount /usr/lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable persist.mount    # 必须 enable，/usr/lib 下的 unit 不会自动生效
```

验证：

```
$ findmnt /persist
TARGET   SOURCE          FSTYPE OPTIONS
/persist /dev/mmcblk0p11 ext4   ro,relatime

$ systemctl is-enabled persist.mount
enabled
$ systemctl list-dependencies local-fs.target | grep persist
● ├─persist.mount
```

内容：

```
-rw------- 1002 1002     9  .bt_nv.bin
-rw-r--r-- 1010 1010 29816  WCNSS_qcom_wlan_nv.bin
drwxr-xr-x root root    aost/
```

## 5. 验证证据

### 设备侧

```
UDC      : ci_hdrc.0
idVendor : 0x05c6
idProduct: 0x90b4
os_desc  : use=1 vendor=0xcd sign=MSFT100
compat_id: RNDIS
subcomp  : 5162001
dev_addr : 02:00:26:e0:41:be      ← 由序列号派生
host_addr: 02:00:26:e0:41:bf
usb0     : UP  192.168.100.1/24  172.16.42.1/16
dnsmasq  : pid 5405 running
nft      : oifname "wwan*" ip saddr 192.168.100.0/24 masquerade
persist  : /dev/mmcblk0p11 on /persist type ext4 (ro,relatime)
```

### Windows 侧

```
=== 设备 ===
Status  Class   FriendlyName
OK      USB     USB Composite Device          USB\VID_05C6&PID_90B4\UFI003-26E041BC
OK      Net     Remote NDIS Compatible Device USB\VID_05C6&PID_90B4&MI_00\...

=== 网卡 ===
Name     : 以太网 3
Desc     : Remote NDIS Compatible Device #2
Status   : Up
Mac      : 02-00-26-E0-41-BF      ← 与 host_addr 一致
LinkSpeed: 426.0 Mbps

=== 地址 ===
192.168.100.95/24   PrefixOrigin=Dhcp  SuffixOrigin=Dhcp
gateway: 192.168.100.1

=== 连通性 ===
ping 192.168.100.1   0 ms x3
TCP  192.168.100.1:22  TcpTestSucceeded=True
SSH banner           SSH-2.0-OpenSSH_10.4
```

> 网卡名从"以太网 2"变成"以太网 3"是改 USB serialnumber 后的一次性副作用，
> 见第 7 节第 5 条。

### 端到端（主机经 4G 上网）

```
ping 223.5.5.5       53 / 45 / 33 ms
Resolve-DnsName      www.baidu.com -> 220.181.111.232
Invoke-WebRequest    http://www.baidu.com -> 200
```

### SSH 登录（从 Windows，经 LAN）

```
$ ssh -i ~/.ssh/ufi003_ed25519 pmos@192.168.100.1 "..."
SSH_AUTH_OK
410stick-ufi003-mb-v02
pmos
6.12.1-msm8916
usb0             UP             192.168.100.1/24 172.16.42.1/16
wwan0            UNKNOWN        10.150.104.12/29
```

### 重启自愈（完整 `reboot` 之后）

```
$ systemctl is-active usb-lan.service   -> active
$ systemctl is-enabled usb-lan.service  -> enabled
$ systemctl is-active persist.mount     -> active
$ findmnt -no TARGET,SOURCE,OPTIONS /persist
/persist /dev/mmcblk0p11 ro,relatime
$ systemctl --failed                    -> (空)
$ ip -4 -br addr show usb0
usb0  UP  192.168.100.1/24 172.16.42.1/16
$ ping -c 2 223.5.5.5
2 packets transmitted, 2 received, 0% packet loss
round-trip min/avg/max = 32.839/33.907/34.975 ms
```

主机侧（重启后，无需任何人工干预）：

```
以太网 3   Up   MAC 02-00-26-E0-41-BF
192.168.100.95/24  PrefixOrigin=Dhcp
ping 223.5.5.5  36 / 32 ms
http://www.baidu.com -> 200
TCP 192.168.100.1:22 -> True
```

> 注意：`/persist` 目录属主是 UID 1000、权限 `771`，普通用户 `pmos` 读不到内容
> （`ls: Permission denied`）。这不影响功能（systemd 以 root 挂载），但需要读
> NV 内容时得用 `sudo`。

## 6. 使用

```sh
# 设备侧
sudo usb-lan.sh up        # 建 gadget + LAN + DHCP + NAT
sudo usb-lan.sh status    # 看 gadget/地址/dnsmasq/MAC 状态
sudo usb-lan.sh mac       # 只打印本机的派生 MAC，不动 gadget
sudo usb-lan.sh down      # 拆掉

systemctl enable usb-lan  # 开机自启（已启用）
```

```powershell
# Windows 侧
ssh -i "$env:USERPROFILE\.ssh\ufi003_ed25519" pmos@192.168.100.1
```

主机拿不到地址时的手动兜底：静态配 `192.168.100.2/24`，网关 `192.168.100.1`；
或走保留的 `172.16.42.2/16`（`172.16.42.1` 仍在本机 usb0 上）。

## 7. 遗留

1. **设备包没有集成这几个文件** —— `usb-lan.sh` / `usb-lan.service` / `persist.mount`
   目前只存在于这台机器上。`config/device-testing/device-410stick-ufi003-mb-v02/APKBUILD`
   的 `source=` 里没有它们，`package()` 也没安装。**所以从 Release 下载 zip 刷机，
   RNDIS 仍然是坏的（`02/06/00`），persist 仍然不挂载。** 这是让本次改动真正"出厂可用"
   的必要一步，未做。
2. **TTL 管理** —— 尚未实现。若目的是让运营商侧看到统一的 TTL（避免共享检测），
   需要在 `nft` 的 `mangle` 表对转发流量做 `ip ttl set 65`；若只是开发期诊断，
   则无需动内核转发路径。
3. **WiFi AP 残留** —— 上一轮实验手工起的 `hostapd` 和它的 `dnsmasq`
   （`/etc/dnsmasq.d/wifi-ap.conf`，`192.168.4.1`）还在，另有两条
   `192.168.4.0/24` 的 masquerade 规则。与 RNDIS 互不影响，重启后裸进程消失。
   需要正式做成服务时再补。
4. **initramfs gadget 交接** —— 开机时 initramfs 会先建一个 `172.16.42.1` 的
   gadget，`usb-lan.service` 起来后再拆掉重建，主机侧会看到一次 USB 断开/重连。
   属预期行为。

   注意：本次把 USB `serialnumber` 从 `ufi003-pmos` 改成了 `ufi003-<序列号>`，
   主机会把它当成新设备，**一次性**新建一块网卡（本机是"以太网 2"→"以太网 3"）。
   之后只要序列号不变就不会再变。

## 8. 一个必须避开的操作：别用 systemd-run 调度 reboot

本次验证时用了：

```sh
sudo systemd-run --on-active=3 --unit=do-reboot --collect systemctl reboot
```

结果是设备进入了 **shutdown 循环**：18 秒内串口打出 50 次完整关机序列，
`systemctl-shutdown` 反复执行，但内核 uptime 一直在涨（57s → 114s），
说明 `reboot(2)` 没有真正复位芯片，而 transient timer 在 `--collect` 回收后
又被重新调度，于是反复请求 `reboot.target`。

期间：

- `ping 192.168.100.1` 通（网络栈还在）
- SSH `Connection refused`（sshd 已被停掉）
- 串口满速刷屏，无法登录
- SysRq 被禁用（`sysrq: This sysrq operation is disabled`），救不回来

最终它自己完成了重启并恢复正常（`systemctl --failed` 为空，两个 unit 都 active），
但中间空转了几分钟，且没有任何干净的恢复手段。

**正确做法**：直接 `sudo systemctl reboot`（接受 SSH 断开），或者

```sh
sudo nohup sh -c 'sleep 3; systemctl reboot' >/dev/null 2>&1 &
```

关键是**不要创建 transient unit**去触发 reboot。
