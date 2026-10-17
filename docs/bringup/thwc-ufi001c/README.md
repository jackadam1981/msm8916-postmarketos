# thwc-ufi001c bring-up evidence

创建时间：2026-10-18 05:31:27

原则：只读优先，先记录和备份，再考虑启动或刷写。

## 目录

- `photos/`: 外壳标签、PCB 正反面、芯片丝印和测试点照片。
- `firmware/`: 原厂 boot 备份、EDL 读出的分区、固件包和校验和。
- `logs/`: USB、fastboot、EDL、串口、内核和 lk2nd 日志。
- `reports/`: `extract_qcom_ids.py` 和 `generate_device_report.py` 生成的报告。

## 最小证据

1. 外壳标签和 PCB 丝印照片。
2. 正常模式、fastboot、9008/EDL 的 USB ID。
3. 分区表输出。
4. 原厂 boot 或 boot_a/boot_b 备份及 SHA-256。
5. 从原厂 DTS 提取的 qcom ID 报告。
6. 首次启动或刷写前的恢复路径说明。
