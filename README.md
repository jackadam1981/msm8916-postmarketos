# MSM8916 PostmarketOS / 标准 Linux 工作台

这个仓库用于整理 MSM8916 OpenStick/UFI 类设备的标准 Linux / postmarketOS 移植工作。当前已经有 `UFI003_MB_V02` 三台和 `QRZL903-1` 两台真机证据，项目进入 lk2nd/lk1st 编译与刷写验证阶段。

当前目标是减少 lk2nd/lk1st 刷写验证中的试错：

1. 保留每台真机的原始备份、身份信息和设备树证据；
2. 明确 `UFI003_MB_V02` 与 `QRZL903-1` 的 lk2nd/lk1st 候选；
3. 生成可复现的 lk2nd/lk1st 构建产物；
4. 按只读备份、可回滚、逐台验证的方式刷写测试。

## 当前状态

- 编译机源码位于 `/home/jack/work/msm8916-standard-linux/third_party/`。
- 已拉取 `lk2nd`、`pmaports`、`pmbootstrap` 作为参考。
- 旧的无真机 lk2nd/lk1st 构建产物已清理，下一轮应按当前真机证据重新构建。
- `UFI003_MB_V02`：三台已刷回 MIKO/UFI003 Android，运行态 DT 均为 MSM8916 512MB MTP / `qcom,board-id=<8 0x100>`。
- `QRZL903-1`：两台已确认；`QRZL903-02` 是原厂 Android 基准，`QRZL903-01` 已从 OpenWrt/Linux GPT 恢复到 Android/MTP GPT。
- 在写入 lk2nd/lk1st 前，仍需确认目标机备份、9008 回滚路径和本轮构建哈希。

## 主要文档

- [源码索引](docs/source-index.md)
- [设备矩阵](docs/device-matrix.md)
- [lk2nd/lk1st 下一阶段计划](docs/lk2nd-lk1st-next-stage.zh-CN.md)
- [标准 Linux bring-up 路线](docs/standard-linux-bringup.zh-CN.md)
- [构建 lk2nd](docs/build-lk2nd.md)
- [固件提取流程](docs/firmware-extraction.zh-CN.md)
- [第一台真机 checklist](docs/first-device-checklist.zh-CN.md)
- [真机 bring-up 证据包](docs/bringup-evidence.zh-CN.md)
- [UFI003_MB_V02 设备清单](docs/ufi003-device-inventory.zh-CN.md)
- [UFI003_MB_V02 救砖包线索](docs/ufi003-rescue-package-research.zh-CN.md)
- [UFI003_MB_V02 设备树证据](docs/ufi003-device-tree-evidence.zh-CN.md)
- [QRZL903-1 设备清单](docs/qrzl903-device-inventory.zh-CN.md)
- [QRZL903-1 bring-up 记录](docs/qrzl903-1-bringup.zh-CN.md)
- [刷写 lk2nd](docs/flashing-lk2nd.zh-CN.md) / [Flashing lk2nd](docs/flashing-lk2nd.md)
- [第三方源码](third_party/README.md)
- [设计规格](docs/superpowers/specs/2026-05-27-msm8916-standard-linux-porting-design.md)

## 安全原则

外壳相似的 MSM8916 设备不一定可以互刷。商品名、外壳标签或卖家描述都不够。必须先从固件或硬件证据确认 `qcom,msm-id`、`qcom,board-id`、启动模式、存储分区和恢复方式。

当前所有标准 Linux 结论仍以“待 lk2nd/lk1st 实机启动验证”为准。Android/原厂固件证据只证明硬件桶、分区布局和回滚路径，不等于标准 Linux 已稳定适配。
