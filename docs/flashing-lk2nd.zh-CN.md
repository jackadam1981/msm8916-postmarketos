# 刷写 lk2nd

本文说明 lk2nd 的常见刷写方式。不要在具体设备上直接套用这些命令，除非已经确认启动模式、分区布局、原厂固件备份和救砖路径。

## 当前构建产物

编译机产物：

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

本地副本：

```text
out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

SHA-256：

```text
02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0
```

## 刷写前必须确认

先完成这些检查：

1. 确认具体主板或候选设备类型。
2. 保存原厂 `boot.img`。
3. 备份所有能读取的分区。
4. 确认设备能否进入 fastboot。
5. 确认 EDL 救砖是否可用。
6. 确认 boot 分区名称和大小。

任意一项未知时都应停止，不要继续刷写。

## 常规 fastboot 流程

如果设备有可用 fastboot，并且已经确认 boot 分区：

```sh
fastboot devices
fastboot flash boot lk2nd-msm8916-ce7fc78.img
fastboot reboot
```

部分设备可能需要 raw 写入：

```sh
fastboot flash:raw boot lk2nd-msm8916-ce7fc78.img
```

如果 stock bootloader 支持临时启动，优先测试临时启动，风险更低：

```sh
fastboot boot lk2nd-msm8916-ce7fc78.img
```

不是所有 stock bootloader 都支持临时启动。

## lk2nd 内部更新流程

当设备已经运行 lk2nd，并进入 lk2nd 自己提供的 fastboot 环境后，可能可以这样更新 lk2nd：

```sh
fastboot flash lk2nd lk2nd-msm8916-ce7fc78.img
```

注意：这个命令面向 lk2nd 的 fastboot 环境，不一定适用于原厂 bootloader。

## EDL 流程

如果必须通过 EDL 写入，并且已经确认分区布局：

```sh
edl w boot lk2nd-msm8916-ce7fc78.img
```

这需要可用的 EDL 工具、兼容的 programmer，并且确认 `boot` 是正确目标分区。

## OpenStick 注意事项

对于本项目关注的 OpenStick/UFI 类设备，当前通用 `lk2nd.img` 很可能通过 MSM8916 QCDT 覆盖多个候选板型。但这不代表所有设备可以随便互刷。

第一台真机建议流程：

1. 备份原厂固件。
2. 提取下游 DTS 和 Qualcomm IDs。
3. 对照 `docs/device-matrix.md`。
4. 如果支持，先尝试临时启动。
5. 确认恢复路径后再刷写。

## 恢复原厂 boot

保留原厂 boot 镜像：

```sh
fastboot flash boot original-boot.img
```

如果通过 EDL 恢复：

```sh
edl w boot original-boot.img
```

具体命令取决于设备和 EDL 工具。
