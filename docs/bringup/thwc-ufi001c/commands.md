# Command Log

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
python3 tools/generate_device_report.py devices/openstick/ufi-001c.yaml \
  --ids-json reports/qcom-ids.json \
  --devices-dir devices/openstick \
  --output reports/device-report.md
```
