# MSM8916 PostmarketOS / 标准 Linux 工作台

整理 MSM8916 OpenStick/UFI 类设备的 postmarketOS 移植与 TF-A/PAS 低层实验。主实验样本：**UFI003-02**（`UFI003_MB_V02`）。

## 当前状态（2026-06-16）

**产品路线：**

```text
Android GPT + TF-A BL31 (tz/tzbak) + U-Boot (aboot) + postmarketOS (system/userdata)
```

- **非 radio 基线已成立**：eMMC、RNDIS、SSH、OpenRC、LED、input
- **Radio 仍 blocked**：`PAS_MSS_RESET=-5`；活跃实验为 **三轨 SMEM phase**（BL31 + kernel kmod）
- **编译机**：`jack@192.168.2.18`（`/home/jack/work/msm8916-standard-linux`）
- **lk2nd/lk1st** 仍为历史实验线，非当前默认刷写目标

详情：[docs/ufi003/current-status.zh-CN.md](docs/ufi003/current-status.zh-CN.md)

## 文档入口

| 读者意图 | 链接 |
| --- | --- |
| **文档总导航（Diataxis）** | [docs/README.zh-CN.md](docs/README.zh-CN.md) |
| **UFI003 实验枢纽** | [docs/ufi003/README.zh-CN.md](docs/ufi003/README.zh-CN.md) |
| **实验总表（status / 日志路径）** | [docs/ufi003/experiments-index.zh-CN.md](docs/ufi003/experiments-index.zh-CN.md) |
| **脚本与刷写** | [tools/README.md](tools/README.md) |
| 设备矩阵 | [docs/device-matrix.md](docs/device-matrix.md) |
| 三台 UFI003 身份与备份 | [docs/ufi003/archive/ufi003-device-inventory.zh-CN.md](docs/ufi003/archive/ufi003-device-inventory.zh-CN.md) |
| 标准 pmOS 分区与刷写 | [docs/ufi003/archive/ufi003-standard-pmos-overall-outline.zh-CN.md](docs/ufi003/archive/ufi003-standard-pmos-overall-outline.zh-CN.md) |
| stage0c+ 闭合状态 | [docs/ufi003/archive/ufi003-stage0c-plus-status-20260614.zh-CN.md](docs/ufi003/archive/ufi003-stage0c-plus-status-20260614.zh-CN.md) |

## 真机样本

| 设备 | 角色 |
| --- | --- |
| UFI003-01 / 02 / 03 | `UFI003_MB_V02`；**02** 为主实验机 |
| QRZL903-01 / 02 | `thwc,ufi001c` 对照 |

## 安全原则

外壳相似的 MSM8916 设备不可互刷。必须以固件/硬件证据确认 `qcom,msm-id`、`qcom,board-id`、分区与 9008 恢复路径。刷写前备份身份分区；**EDL 写 tz 前必须确认 serial 与确认码**。

## 健康检查

```bash
python3 -m compileall tools
python3 tools/lib/validate_device_metadata.py devices/openstick
```

Windows：`powershell -File tools/lib/ufi003_health_check.ps1`

## 设计规格

[docs/superpowers/specs/2026-05-27-msm8916-standard-linux-porting-design.md](docs/superpowers/specs/2026-05-27-msm8916-standard-linux-porting-design.md)
