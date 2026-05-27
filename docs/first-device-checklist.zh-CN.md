# 第一台真机 checklist

收到真机后，先记录和备份，再考虑启动或刷写。

## 1. 外观和硬件记录

- 拍摄外壳标签。
- 拍摄 PCB 正反面。
- 记录所有可见丝印、板号、版本号。
- 记录存储芯片、射频/基带、Wi-Fi/BT 芯片标识。
- 记录是否有按键、测试点、天线座、SIM 卡座、TF 卡座。

## 2. USB 模式记录

在不同模式下记录 USB ID：

```sh
lsusb
```

需要记录：

- 正常开机模式
- fastboot 模式
- Qualcomm 9008/EDL 模式
- 其他 vendor 工具模式

## 3. 只读备份

优先确认 9008/EDL 能否读取分区表：

```sh
edl printgpt
```

如果能读取，先备份 boot：

```sh
edl r boot original-boot.img
sha256sum original-boot.img
```

如果存在 A/B 分区：

```sh
edl r boot_a boot_a.img
edl r boot_b boot_b.img
sha256sum boot_a.img boot_b.img
```

在没有备份前，不写任何分区。

## 4. 固件和设备树提取

从原厂 `boot.img` 或固件包中提取 DTB/DTS，并生成 ID 报告：

```sh
python3 tools/extract_qcom_ids.py vendor.dts --pretty > qcom-ids.json
python3 tools/generate_device_report.py devices/openstick/ufi-001c.yaml \
  --ids-json qcom-ids.json \
  --devices-dir devices/openstick \
  --output report.md
```

记录：

- `qcom,msm-id`
- `qcom,board-id`
- `qcom,pmic-id`
- cmdline
- panel 名称
- storage 类型
- modem/Wi-Fi 相关节点

## 5. 候选匹配

对照：

- `docs/device-matrix.md`
- `docs/source-index.md`
- `devices/openstick/*.yaml`
- `out/lk2nd-variants/manifest.psv`

只有当 firmware ID、cmdline、硬件信息都接近时，才把状态从 `buildable-unverified` 提升到 `firmware-identified`。

## 6. 启动测试顺序

推荐顺序：

1. 只读识别和备份。
2. 如果 stock bootloader 支持，先尝试 `fastboot boot`。
3. 如果必须写入，先确认能通过 EDL 恢复原厂 boot。
4. 首次写入只写 boot，不碰 modem、tz、rpm、aboot 等底层固件。

## 7. 禁止事项

- 未备份原厂 boot 前禁止写 boot。
- 未确认分区表前禁止 `edl w`。
- 未确认设备型号前禁止跨板刷底层固件。
- 不把“能编译”当成“真机能启动”。
- 不把“外壳相似”当成“设备树通用”。
