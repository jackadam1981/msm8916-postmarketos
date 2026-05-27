# 真机 bring-up 证据包

收到第一台设备后，建议先为它创建一个本地证据包。证据包放在 `out/` 下，默认不会提交到 git，适合保存照片、固件备份、日志和生成报告。

## 创建目录

```sh
python3 tools/create_bringup_case.py \
  --device-id thwc-ufi001c \
  --output out/bringup
```

生成结构：

```text
out/bringup/thwc-ufi001c/
  README.md
  commands.md
  notes.md
  firmware/
  logs/
  photos/
  reports/
```

## 使用原则

- `photos/` 保存外壳、PCB、芯片丝印、测试点照片。
- `firmware/` 保存只读备份，例如原厂 `boot.img`、`boot_a.img`、`boot_b.img` 和 `SHA256SUMS`。
- `logs/` 保存命令输出，例如 `lsusb`、`edl printgpt`、fastboot、串口和 lk2nd 日志。
- `reports/` 保存 DTS、`qcom-ids.json` 和设备报告。

证据包不是最终文档，而是把现场信息收拢起来。等确认设备身份后，再把可公开、可复现的小量事实回填到 `devices/openstick/*.yaml` 和 `docs/device-matrix.md`。

## 元数据校验

修改 `devices/openstick/*.yaml` 或 lk2nd variant 后，运行：

```sh
python3 tools/validate_device_metadata.py devices/openstick \
  --variants-script scripts/build_lk2nd_variants.sh
```

这个检查会确认：

- 每个设备文件包含必需字段。
- 设备 ID 没有重复。
- 状态值在已定义范围内。
- `lk2nd.compatible` 能被当前 variant 构建脚本覆盖。

如果某台真机确认了新的 compatible 或设备树，应先更新构建脚本和设备 YAML，再重新运行校验。
