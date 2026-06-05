# MSM8916 PostmarketOS / 标准 Linux 工作台

这个仓库用于整理 MSM8916 OpenStick/UFI 类设备的移植准备工作。当前还没有真机，所以重点是把源码、候选板型、构建产物和刷写风险先梳理清楚。

当前目标是减少拿到真机或原厂固件后的试错：

1. 索引相关上游源码；
2. 整理已知 MSM8916 4G stick 候选板型；
3. 准备固件提取和 Qualcomm ID 校验流程；
4. 记录 lk2nd 和 postmarketOS 的接入点。

## 当前状态

- 编译机源码位于 `/home/jack/work/msm8916-standard-linux/third_party/`。
- 已拉取 `lk2nd`、`pmaports`、`pmbootstrap` 作为参考。
- 已构建 MSM8916 通用 lk2nd 候选镜像和多个 lk1st 板型候选镜像。
- 还没有真机验证。
- 在确认原厂固件、board ID、分区布局和救砖路径前，任何刷机命令都不能视为安全。

## 主要文档

- [源码索引](docs/source-index.md)
- [设备矩阵](docs/device-matrix.md)
- [标准 Linux bring-up 路线](docs/standard-linux-bringup.zh-CN.md)
- [构建 lk2nd](docs/build-lk2nd.md)
- [固件提取流程](docs/firmware-extraction.zh-CN.md)
- [第一台真机 checklist](docs/first-device-checklist.zh-CN.md)
- [真机 bring-up 证据包](docs/bringup-evidence.zh-CN.md)
- [UFI003_MB_V02 救砖包线索](docs/ufi003-rescue-package-research.zh-CN.md)
- [刷写 lk2nd](docs/flashing-lk2nd.zh-CN.md) / [Flashing lk2nd](docs/flashing-lk2nd.md)
- [第三方源码](third_party/README.md)
- [设计规格](docs/superpowers/specs/2026-05-27-msm8916-standard-linux-porting-design.md)

## 安全原则

外壳相似的 MSM8916 设备不一定可以互刷。商品名、外壳标签或卖家描述都不够。必须先从固件或硬件证据确认 `qcom,msm-id`、`qcom,board-id`、启动模式、存储分区和恢复方式。

当前所有设备树和镜像只到“源码候选 / 可编译”阶段，没有真机验证，不能视为稳定适配。
