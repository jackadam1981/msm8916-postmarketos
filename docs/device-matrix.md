# 设备矩阵

本文记录 MSM8916 4G stick 的候选、真机证据和下一步验证目标。源码线索、Android 原厂证据和标准 Linux 启动状态分开记录。

## 状态定义

| 状态 | 含义 |
| --- | --- |
| `source-candidate` | 上游源码或可信参考中存在，但本地还没有真机/固件证明。 |
| `buildable-unverified` | 已能编译出镜像，但没有固件匹配或真机启动证明。 |
| `firmware-identified` | 已检查 vendor 固件并提取 ID。 |
| `hardware-identified` | 已记录真机板号、USB ID、启动模式和恢复路径。 |
| `lk2nd-selected` | lk2nd/lk1st 已选择预期设备节点。 |
| `linux-boots` | 标准 Linux 能进入 userspace。 |

## MSM8916 4G Stick 候选

| 候选 | lk2nd compatible | lk2nd DTS | 源码线索 | 当前状态 | 第一项验证 |
| --- | --- | --- | --- | --- | --- |
| Unknown 4G modem stick group: UFI_001B/C, UFI003_MB_V02, MF601 | `zhihe,various` | `msm8916-512mb-mtp.dts` | `QCOM_ID_MSM8916 0`，`QCOM_BOARD_ID_MTP 0x100`，共享 cmdline panel 匹配 | `buildable-unverified` | 提取 vendor DTS，确认 board ID/cmdline。 |
| UFI-001C / UFI-001B | `thwc,ufi001c` | `msm8916-512mb-mtp.dts` | 同一个 bundle DTB；上游建议 lk1st 固定 compatible | `buildable-unverified` | 需要真实 UFI-001C/001B 板号或原厂固件证据。 |
| QRZL903-1 | `thwc,ufi001c` | `msm8916-512mb-mtp.dts` | 两台样本已确认；01 曾为 OpenWrt/Linux GPT 且 boot DTB root compatible 为 `thwc,ufi001c`，现已恢复 Android；02 是 2022-06-15 原厂 Android/MTP 基准 | `hardware-identified` | 构建并测试 `thwc,ufi001c` lk1st；保留 9008 Android 恢复路径。 |
| UFI003_MB_V02 | `zhihe,various` | `msm8916-512mb-mtp.dts` | 三台真机刷回 3.53G MIKO/UFI003 后运行态 DT 一致：`qcom,board-id=<8 0x100>`，512MB MTP，ST7735S SPI panel bootargs | `hardware-identified` | 构建并测试通用 `zhihe,various` lk2nd/lk1st；必要时再评估是否固定 compatible。 |
| MF601 | `zhihe,various` | `msm8916-512mb-mtp.dts` | 同属 512MB MTP 通用桶；lk2nd 记录误识别 MF601 时的 reset GPIO 34 和可选 WPS GPIO 107 | `buildable-unverified` | 确认板号、按键和原厂固件 ID。 |
| UZ801 v3.0 | `yiming,uz801-v3` | `msm8916-512mb-mtp.dts` | 同一个 bundle DTB，加 DSI JDI 1080p cmdline 匹配 | `buildable-unverified` | 确认 panel cmdline，以及 stock aboot 是否有 qhypstub/TZ 兼容问题。 |
| JZ0145 v33 | `xiaoxun,jz0145-v33` | `msm8916-512mb-mtp.dts` | 同一个 bundle DTB，加 DSI ST7796S 320p cmdline 匹配 | `buildable-unverified` | 确认 panel cmdline 和 GPIO 37 EDL 键行为。 |
| UF896 | `thwc,uf896` | `msm8916-512mb-qrd-skuh.dts` | `QCOM_ID_MSM8916 0`，QRD SKUH board ID，包含 `0x100`/`0x104` 变体 | `buildable-unverified` | 提取 vendor DTS，确认准确 QRD board tuple。 |

## postmarketOS 基线

对于 MSM8916 4G stick，除非找到更具体的设备包，否则先以 pmaports 的通用路径作为起点：

| 层级 | 候选包/路径 | 作用 |
| --- | --- | --- |
| 设备包 | `device/testing/device-qcom-msm8916` | MSM8916/MSM8939 通用包，带 fastboot 和 lk2nd extlinux 支持。 |
| Kernel 包 | `device/testing/linux-postmarketos-qcom-msm8916` | 使用 msm8916-mainline Linux fork，并安装 DTB。 |
| SoC 包 | `device/testing/soc-qcom-msm8916` | 通用 GPU/audio/remoteproc/modem 支持。 |

## 下一阶段 checklist

1. 重新构建本轮 lk2nd/lk1st，记录源码提交、命令和 SHA-256。
2. 先选一台可回滚样本做刷写验证。
3. 刷写前确认该样本的 EDL 备份、Android 恢复路径和当前 IMEI/MAC。
4. 优先测试 `QRZL903-1` 的 `thwc,ufi001c` lk1st，以及 `UFI003_MB_V02` 的 `zhihe,various` 通用路径。
5. 每次刷写后记录 USB 枚举、串口/屏幕迹象、能否进 fastboot/lk2nd、能否回 9008。
