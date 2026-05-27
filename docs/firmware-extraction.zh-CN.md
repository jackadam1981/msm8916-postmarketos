# 固件提取流程

本文记录拿到原厂 `boot.img` 或完整固件包后的只读分析流程。目标是提取下游 DT 信息，判断设备更像哪个 lk2nd 候选，而不是直接刷写。

## 输入文件

常见输入：

- 原厂 `boot.img`
- 完整 vendor 固件包
- 9008/EDL 备份出来的 `boot` 分区
- 已经提取出的 DTB/DTS 文件

把输入文件放在：

```text
firmware/<device-or-source-name>/
```

`firmware/` 默认被 git 忽略，不要提交原厂二进制固件。

## 推荐流程

1. 为设备建目录，例如 `firmware/ufi001c-sample/`。
2. 放入原厂 `boot.img`。
3. 准备提取工作区：

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools/extract_bootimg.ps1 `
     -InputImage firmware/ufi001c-sample/boot.img `
     -OutputDirectory out/firmware/ufi001c-sample
   ```

4. 使用 `magiskboot`、`unpackbootimg` 等工具拆 boot image。
5. 从 boot image 或附加区域中提取 DTB/DTBO。
6. 使用 `dtc` 反编译：

   ```sh
   dtc -I dtb -O dts -o out/firmware/ufi001c-sample/vendor.dts out/firmware/ufi001c-sample/vendor.dtb
   ```

7. 提取 Qualcomm ID：

   ```sh
   python3 tools/extract_qcom_ids.py out/firmware/ufi001c-sample/vendor.dts --pretty \
     > out/firmware/ufi001c-sample/qcom-ids.json
   ```

8. 和候选设备元数据生成报告：

   ```sh
   python3 tools/generate_device_report.py devices/openstick/ufi-001c.yaml \
     --ids-json out/firmware/ufi001c-sample/qcom-ids.json \
     --devices-dir devices/openstick \
     --output out/firmware/ufi001c-sample/report.md
   ```

## 判断原则

- `qcom,msm-id` / `qcom,board-id` 只说明 bootloader 设备树匹配可能性。
- `qcom,pmic-id`、cmdline、GPIO、panel、Wi-Fi、modem、分区表也要一起看。
- 只有源码候选和 ID 接近时，不能认为设备树稳定。
- 没有原厂 boot 备份和 9008/fastboot 恢复路径时，不要刷写。

## 常用工具

| 工具 | 用途 |
| --- | --- |
| `magiskboot` | 解包 Android boot image，常用于提取 kernel/ramdisk/dtb。 |
| `unpackbootimg` | 解包 Android boot image。 |
| `dtc` | DTB 和 DTS 互转。 |
| `edl` | Qualcomm 9008/EDL 读写分区。 |
| `fastboot` | fastboot 模式刷写/临时启动。 |

这些工具的参数和兼容性会随设备变化。实际使用前先对照工具文档和设备输出。
