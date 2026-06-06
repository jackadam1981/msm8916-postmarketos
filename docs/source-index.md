# 源码索引

本文记录当前阶段最有用的上游源码和本地源码状态。真机证据见设备清单和 bring-up 文档；本文件只说明源码入口与候选关系。

## 编译机工作区

```text
/home/jack/work/msm8916-standard-linux/third_party/
```

| 源码 | 本地路径 | 上游 | 状态 |
| --- | --- | --- | --- |
| lk2nd | `lk2nd` | `https://github.com/msm8916-mainline/lk2nd.git` | 浅克隆，`main`，`ce7fc78` |
| pmaports | `pmaports` | `https://gitlab.postmarketos.org/postmarketOS/pmaports.git` | 浅克隆，`main`，`02ad959` |
| pmbootstrap | `pmbootstrap` | `https://gitlab.postmarketos.org/postmarketOS/pmbootstrap` | `main` archive，无 git 历史 |

Linux kernel 还没有拉取。pmaports 里的 MSM8916 kernel 包当前指向 `https://github.com/msm8916-mainline/linux`，tag 形如 `v6.12.1-msm8916`。首轮先验证 lk2nd/lk1st 选择；进入 kernel/rootfs 阶段后再拉取内核树更合适。

## lk2nd MSM8916 结构

关键路径：

| 用途 | 路径 |
| --- | --- |
| MSM8916 DTS 目录 | `lk2nd/device/dts/msm8916/` |
| MSM8916 DTS 构建列表 | `lk2nd/device/dts/msm8916/rules.mk` |
| lk2nd MSM8916 project | `project/lk2nd-msm8916.mk` |
| lk1st MSM8916 project | `project/lk1st-msm8916.mk` |
| MSM8916 platform 代码 | `platform/msm8916/` |
| MSM8916 target 代码 | `target/msm8916/` |

上游已包含的 4G stick 候选：

| DTS | 型号 / compatible | 匹配信息 | 说明 |
| --- | --- | --- | --- |
| `msm8916-512mb-mtp.dts` | `Unknown 4G Modem Stick`, `zhihe,various` | `qcom,msm-id = <QCOM_ID_MSM8916 0>`，`qcom,board-id = <QCOM_BOARD_ID_MTP 0x100>` | UFI_001B/C、UFI003_MB_V02、MF601 的通用桶。上游说明这些设备 cmdline 相同，lk2nd 很难自动区分。 |
| `msm8916-512mb-mtp.dts` | `ufi-001c/ufi-001b 4G Modem Stick`, `thwc,ufi001c` | 同一个 bundle DTB | 适合 lk1st 固定 `LK2ND_COMPATIBLE="thwc,ufi001c"`。 |
| `msm8916-512mb-mtp.dts` | `QRZL903-1` | 样本 01 boot DTB root compatible 为 `thwc,ufi001c`；样本 02 原厂 Android 运行态仍是 `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` | 实物丝印单独记录为 QRZL903-1；样本 02 的原厂整盘备份可作为恢复基准，但标准 Linux 方向仍优先验证上游 `thwc,ufi001c`。 |
| `msm8916-512mb-mtp.dts` | `UFI003_MB_V02` | 同一个 `zhihe,various` 通用桶；三台真机运行态 DT 均为 `qcom,board-id=<8 0x100>` | 上游注释提到该板，但当前 lk2nd 没有单独 compatible 节点；本地证据见 `docs/ufi003-device-tree-evidence.zh-CN.md`。 |
| `msm8916-512mb-mtp.dts` | `MF601` | 同一个 `zhihe,various` 通用桶 | 上游注释提到该板，并给误识别 MF601 的 reset/WPS GPIO 留了信息。 |
| `msm8916-512mb-mtp.dts` | `uz801 v3.0 4G Modem Stick`, `yiming,uz801-v3` | 同一个 bundle DTB，加 cmdline 匹配 | 上游说明 stock aboot 可能和 qhypstub/db410c TZ firmware 不兼容，尽量使用 lk1st。 |
| `msm8916-512mb-mtp.dts` | `JZ0145 v33 4G Modem Stick`, `xiaoxun,jz0145-v33` | 同一个 bundle DTB，加 cmdline 匹配 | lk2nd 元数据中记录 GPIO 37 可作为 EDL 键。 |
| `msm8916-512mb-qrd-skuh.dts` | `uf896 4G Modem Stick`, `thwc,uf896` | `qcom,msm-id = <QCOM_ID_MSM8916 0>`，多个 QRD SKUH board ID，子类型 `0x100`/`0x104` | 适合 lk1st 固定 `LK2ND_COMPATIBLE="thwc,uf896"`。 |

上游 `rules.mk` 已经把 `msm8916-512mb-mtp.dtb` 和 `msm8916-512mb-qrd-skuh.dtb` 放进 `QCDTBS`。所以拿到真机后的第一步大概率是识别和选择已有候选，而不是立刻新增 DTS。注意：这些只是源码候选，不能等同于已验证设备树。

## pmaports MSM8916 结构

关键路径：

| 用途 | 路径 |
| --- | --- |
| 通用 MSM8916 设备包 | `device/testing/device-qcom-msm8916/` |
| MSM8916 kernel 包 | `device/testing/linux-postmarketos-qcom-msm8916/` |
| MSM8916 通用 SoC 包 | `device/testing/soc-qcom-msm8916/` |

已观察到的包信息：

| 包 | 关键信息 |
| --- | --- |
| `device-qcom-msm8916` | MSM8916/MSM8939 通用设备包，`aarch64`，fastboot 刷写方式，支持 lk2nd extlinux，`deviceinfo_dtb_extlinux="qcom/msm8*16-* qcom/msm8*39-* qcom/apq8016-* apq8039-*"`, `deviceinfo_partition_type="msdos"`，原因是 lk2nd 还不支持 SD 卡/子分区 GPT。 |
| `linux-postmarketos-qcom-msm8916` | kernel 包使用 `https://github.com/msm8916-mainline/linux`，版本 `6.12.1`，tag 形如 `v6.12.1-msm8916`，支持 `aarch64` 和 `armv7`。 |
| `soc-qcom-msm8916` | 通用 SoC 包包含 Adreno A306 workaround、UCM 音频、remoteproc/modem、q6voiced 配置和 WirePlumber S16_LE workaround。 |

## lk2nd/lk1st 阶段优先级

1. 在编译机重新构建本轮 `lk2nd-msm8916` 和必要的 lk1st 固定 compatible 产物。
2. 记录每个产物对应的源码提交、构建命令、文件名和 SHA-256。
3. 以 `QRZL903-1` 的 `thwc,ufi001c` 和 `UFI003_MB_V02` 的 `zhihe,various` 为首轮目标。
4. 刷写前复核对应样本的设备清单、EDL 备份和 Android 回滚路径。
