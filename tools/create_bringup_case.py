#!/usr/bin/env python3
"""Create a local first-device bring-up evidence folder."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def write_text_once(path: Path, text: str) -> None:
    if path.exists():
        return
    path.write_text(text, encoding="utf-8")


def create_case(device_id: str, output: Path) -> Path:
    case_dir = output / device_id
    logs_dir = case_dir / "logs"
    firmware_dir = case_dir / "firmware"
    photos_dir = case_dir / "photos"
    reports_dir = case_dir / "reports"

    for directory in (logs_dir, firmware_dir, photos_dir, reports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_text_once(
        case_dir / "README.md",
        f"""# {device_id} bring-up evidence

创建时间：{created_at}

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
""",
    )

    write_text_once(
        case_dir / "commands.md",
        """# Command Log

把真实输出粘贴到 `logs/` 下对应文件，不要只保留截图。

## USB 模式

```sh
lsusb | tee logs/lsusb-normal.txt
lsusb | tee logs/lsusb-fastboot.txt
lsusb | tee logs/lsusb-edl.txt
```

## EDL 只读检查

```sh
edl printgpt | tee logs/edl-printgpt.txt
edl r boot firmware/original-boot.img
sha256sum firmware/original-boot.img | tee firmware/SHA256SUMS
```

如果是 A/B 分区：

```sh
edl r boot_a firmware/boot_a.img
edl r boot_b firmware/boot_b.img
sha256sum firmware/boot_a.img firmware/boot_b.img | tee firmware/SHA256SUMS
```

## DTS 和报告

```sh
dtc -I dtb -O dts -o reports/vendor.dts reports/vendor.dtb
python3 tools/extract_qcom_ids.py reports/vendor.dts --pretty > reports/qcom-ids.json
python3 tools/generate_device_report.py devices/openstick/ufi-001c.yaml \\
  --ids-json reports/qcom-ids.json \\
  --devices-dir devices/openstick \\
  --output reports/device-report.md
```
""",
    )

    write_text_once(
        case_dir / "notes.md",
        """# Notes

## 硬件

- 板号：
- 存储：
- 内存：
- Wi-Fi/BT：
- SIM/TF：
- 按键/测试点：

## 启动模式

- 正常模式 USB ID：
- fastboot USB ID：
- EDL USB ID：

## 风险

- 未确认事项：
- 不可刷写分区：
- 恢复路径：
""",
    )

    return case_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a first-device bring-up evidence folder.")
    parser.add_argument("--device-id", required=True, help="Device id or case name, for example thwc-ufi001c")
    parser.add_argument("--output", type=Path, default=Path("out/bringup"), help="Output directory")
    args = parser.parse_args()

    case_dir = create_case(args.device_id, args.output)
    print(f"Created bring-up case: {case_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
