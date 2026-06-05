# 设备矩阵

本文记录真机到手前的候选设备。这里的值是源码线索，不等于某台实体设备已经匹配。

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
| UFI-001C / UFI-001B | `thwc,ufi001c` | `msm8916-512mb-mtp.dts` | 410 原版 Android ADB 采集显示 `ro.build.cust_proj=UFI001C`，runtime DT 为 MSM 8916 512MB MTP，`qcom,board-id=<8 0x100>`；上游建议 lk1st 固定 compatible | `firmware-identified` | 补 PCB 照片、板号、USB 模式和 GPIO 37 EDL 键行为。 |
| UFI003_MB_V02 | `zhihe,various` | `msm8916-512mb-mtp.dts` | 与 UFI_001B/C、MF601 同属 512MB MTP 通用桶 | `buildable-unverified` | 确认板号，并查是否存在当前 lk2nd 之外的固定 compatible。 |
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

## 第一台真机 checklist

1. 拍摄 PCB 丝印和外壳标签。
2. 记录正常模式、fastboot、EDL 下的 USB ID。
3. 刷写前备份可读取分区。
4. 保存原厂 `boot.img` 和完整固件包。
5. 提取 DTB/DTS，并记录 `qcom,msm-id`、`qcom,board-id`、`qcom,pmic-id`。
6. 对照上面的 lk2nd 候选。
7. 如果上游说明 lk2nd 无法自动区分变体，优先测试 lk1st 固定 compatible。
