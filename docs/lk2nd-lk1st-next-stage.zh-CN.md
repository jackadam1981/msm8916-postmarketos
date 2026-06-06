# lk2nd/lk1st 下一阶段计划

本文是进入标准 Linux 刷写验证前的工作入口。历史无真机阶段的旧构建产物不再作为本轮依据；下一轮应在编译机按当前源码和真机证据重新构建。

## 当前真机基线

| 设备 | 样本 | 当前状态 | 首选 lk2nd/lk1st 方向 | 回滚依据 |
| --- | --- | --- | --- | --- |
| `QRZL903-1` | `QRZL903-01` | 已恢复 Android/MTP，ADB `a33fbfc` | `thwc,ufi001c` lk1st | `docs/qrzl903-device-inventory.zh-CN.md` |
| `QRZL903-1` | `QRZL903-02` | 原厂 Android/MTP 基准，ADB `d0b1d17` | 保留为恢复基准，暂不优先刷写 | `out/bringup/qrzl903-02/edl-20260606/full-emmc-stock-android-20260606.bin` |
| `UFI003_MB_V02` | `UFI003-01/02/03` | 已刷回 MIKO/UFI003 Android | `zhihe,various` 通用 lk2nd/lk1st | `docs/ufi003-device-inventory.zh-CN.md` |

## 构建目标

| 目标 | compatible / 配置 | 用途 |
| --- | --- | --- |
| `lk2nd-msm8916.img` | 上游 QCDT bundle | 通用链路验证，适合先看是否能进入 lk2nd/fastboot |
| `thwc-ufi001c-lk1st-msm8916.mbn` | `LK2ND_COMPATIBLE=thwc,ufi001c` | `QRZL903-1` 首选固定目标 |
| `zhihe-various-lk1st-msm8916.mbn` | `LK2ND_COMPATIBLE=zhihe,various` | `UFI003_MB_V02` 首选固定目标 |

## 构建前检查

1. 编译机路径只使用 `/home/jack/work/msm8916-standard-linux/`。
2. 记录 `third_party/lk2nd` 的 `git rev-parse HEAD`。
3. 清理旧 `out/lk2nd-*` 产物后重新构建。
4. 产物命名使用日期和目标名，不使用短提交作为主要人类标识。
5. 每个产物生成 SHA-256 manifest。

## 刷写前检查

1. 只选择一台样本进入首刷。
2. 记录刷写前 ADB serial、IMEI、Wi-Fi MAC、当前 USB 模式。
3. 确认 9008 可进入，且 EDL loader 能 `printgpt`。
4. 确认对应 Android 恢复镜像或分区备份存在。
5. 刷写命令写入日志，刷写后立即记录 USB 枚举和是否可回滚。

## 首轮建议

1. 先用 `QRZL903-01` 测 `thwc,ufi001c` lk1st。
2. 成功进入 lk2nd/fastboot 后，再测试通用 `lk2nd-msm8916.img` 或 postmarketOS 启动链。
3. `QRZL903-02` 暂时作为原厂恢复基准，不做首轮刷写。
4. `UFI003_MB_V02` 首刷前再选一台状态最清楚的样本，优先不动三台里证据最完整的一台。

## 结果记录

每次刷写后更新：

- `docs/qrzl903-device-inventory.zh-CN.md` 或 `docs/ufi003-device-inventory.zh-CN.md`
- `docs/device-matrix.md`
- 对应 `devices/openstick/*.yaml`

记录至少包括：

- 构建产物路径和 SHA-256
- 写入方式和目标分区
- USB 枚举结果
- lk2nd/fastboot/串口/屏幕现象
- 回滚结果
