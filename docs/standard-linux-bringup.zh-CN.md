# 标准 Linux bring-up 路线

本文记录 MSM8916 OpenStick/UFI 类设备在确认身份后的标准 Linux 推进顺序。当前还没有真机，所以这里只定义可复用流程，不声称任何板型已经能启动 Linux。

## 阶段 0：身份确认

目标是证明“这台机器是谁”，而不是证明“某个镜像能刷”。

必须收集：

- 板号、PCB 版本和关键芯片照片。
- 正常模式、fastboot、9008/EDL 的 USB ID。
- 原厂 boot 或 boot_a/boot_b 备份。
- 分区表输出。
- vendor DTS 中的 `qcom,msm-id`、`qcom,board-id`、`qcom,pmic-id`。
- cmdline、panel、存储、Wi-Fi/BT、modem 相关节点。

完成后更新：

- `devices/openstick/<device>.yaml`
- `docs/device-matrix.md`
- `out/bringup/<device>/reports/device-report.md`

## 阶段 1：lk2nd / lk1st 选择

优先目标是让 bootloader 选择预期设备树。

推荐顺序：

1. 如果原厂 bootloader 支持临时启动，优先尝试 `fastboot boot`。
2. 如果上游说明设备难以自动识别，优先使用固定 compatible 的 lk1st variant。
3. 首次写入只碰 boot 相关分区，不碰 modem、tz、rpm、aboot 等底层固件。
4. 每次测试都保存串口、USB、fastboot 或 EDL 输出。

当前已可构建的候选见：

- `docs/build-lk2nd.md`
- `out/lk2nd-variants/manifest.psv`

## 阶段 2：最小 Linux 启动

目标是进入一个最小 userspace，先不追求完整功能。

建议最小集合：

- lk2nd 能加载 kernel、initramfs 和 DTB。
- kernel cmdline 可见。
- USB gadget 或串口至少有一种可交互通道。
- rootfs 可以是 initramfs、postmarketOS、Debian 或 Alpine 的最小系统。

优先验证：

- CPU/内存初始化。
- eMMC/SD 存储识别。
- USB device/host 行为。
- regulator 和 GPIO 是否有明显错误。
- reboot、poweroff、EDL 进入方式。

暂缓验证：

- modem 数据业务。
- Wi-Fi/BT。
- 音频。
- GPU。
- 省电和热管理。

## 阶段 3：DTS 收敛

不要直接从外壳型号推 DTS。标准 Linux DTS 应从这些证据收敛：

- 原厂 vendor DTS。
- 上游 lk2nd DTS。
- msm8916-mainline Linux DTS。
- PCB 丝印和芯片型号。
- 真机启动日志。

本仓库可先把小型 DTS 实验和说明放在 `linux/dts/`。真正可复用后，再整理成补丁或提交到合适的上游项目。

## 阶段 4：rootfs 选择

rootfs 先服务于 bring-up，不要过早绑定发行版。

| 方向 | 适合阶段 | 说明 |
| --- | --- | --- |
| initramfs | 最早期 | 体积小，便于验证 kernel、DTB、USB 和存储。 |
| postmarketOS | 中期 | pmaports 已有 MSM8916 通用设备包和 lk2nd extlinux 经验。 |
| Debian/Alpine | 中后期 | 更接近通用服务器/网关用途，但需要先稳定 kernel 和启动链。 |
| OpenWrt | 后期 | 适合 4G stick/路由用途，但应在硬件基础稳定后再做。 |

## 阶段 5：状态提升条件

状态不要靠猜测提升。

| 新状态 | 最低证据 |
| --- | --- |
| `firmware-identified` | 已保存原厂固件或 boot 备份，DTS ID 报告和设备 YAML 一致。 |
| `hardware-identified` | 已记录板号、USB ID、启动模式、恢复路径。 |
| `lk2nd-selected` | 日志证明 lk2nd/lk1st 选择了预期 compatible 或 DTB。 |
| `linux-boots` | 标准 Linux 进入 userspace，并保存启动日志。 |

任何阶段发现 ID、panel、存储或 GPIO 不一致，都应退回候选状态，不要为了复用现有板型而硬套。
