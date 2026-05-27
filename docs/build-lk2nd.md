# 构建 lk2nd

本项目在 Linux 编译机上构建 lk2nd，不在 Windows 工作区直接编译。

## 编译机路径

```text
/home/jack/work/msm8916-standard-linux/third_party/lk2nd
```

## 最小依赖

编译机使用 Debian。当前 lk2nd 构建只需要安装这些包：

```sh
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  gcc-arm-none-eabi \
  binutils-arm-none-eabi \
  device-tree-compiler
```

使用 `--no-install-recommends` 可以避免拉取很大的 `libstdc++-arm-none-eabi-newlib` 推荐包。当前 lk2nd 构建不需要它。

## 通用 lk2nd 构建命令

```sh
cd /home/jack/work/msm8916-standard-linux/third_party/lk2nd
rm -rf build-lk2nd-msm8916
make -j$(nproc) TOOLCHAIN_PREFIX=arm-none-eabi- lk2nd-msm8916
```

## 板型 variant 构建脚本

构建 OpenStick/UFI 候选板型时使用项目脚本：

```sh
cd /home/jack/work/msm8916-standard-linux
sh scripts/build_lk2nd_variants.sh --list
sh scripts/build_lk2nd_variants.sh
```

产物按“板型/配置 + 构建目标 + 日期”命名：

```text
<board>-<build-target>-YYYYMMDD.<img|mbn>
```

lk2nd 源码 commit 不放进文件名，而是记录在 `manifest.psv` 里。

## 已验证可编译的通用构建

构建输入：

- lk2nd 上游：`https://github.com/msm8916-mainline/lk2nd.git`
- 分支：`main`
- commit：`ce7fc78`
- 编译器：`arm-none-eabi-gcc (15:14.2.rel1-1) 14.2.1 20241119`
- dtc：`DTC 1.7.2`

生成产物只证明源码和工具链可编译，不证明任何真机可启动。

生成产物：

| 文件 | 大小 | SHA-256 |
| --- | --- | --- |
| `build-lk2nd-msm8916/lk2nd.img` | 407K | `02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0` |
| `build-lk2nd-msm8916/qcdt.img` | 126K | `237decb1fc9d2594796031b9991f32bfd8ef19e837148e2c5887e0acd1731359` |

QCDT 镜像包含 44 个 DTB，其中包括：

- `msm8916-512mb-mtp.dtb`
- `msm8916-512mb-qrd-skuh.dtb`

通用候选产物已复制到编译机：

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-msm8916/lk2nd-msm8916-ce7fc78.img
```

在确认设备固件、board ID、分区布局和恢复路径前，不要把该镜像刷入真机。

## 已验证可编译的板型候选构建

编译机输出目录：

```text
/home/jack/work/msm8916-standard-linux/out/lk2nd-variants/
```

本地副本：

```text
out/lk2nd-variants/
```

`20260527` 构建产物。它们是候选镜像，尚未经过真机或原厂固件验证：

| 文件 | 用途 | SHA-256 |
| --- | --- | --- |
| `generic-lk2nd-msm8916-20260527.img` | MSM8916 通用 lk2nd QCDT 候选镜像 | `02125c383b2a295907fe781067e065b72111b315fb6be0d0ac2f8dafb378a9d0` |
| `zhihe-various-lk1st-msm8916-20260527.mbn` | UFI_001B/C、UFI003_MB_V02、MF601 的通用 lk1st 候选配置 | `40a345f9f6e8a86de2cdf8919826976c809de2eaa628e61190bc4002483c3ab8` |
| `ufi001c-lk1st-msm8916-20260527.mbn` | UFI-001B/C lk1st 候选配置 | `63c6f7f39ec634a30aa46018a61c25de5fbf21932b2a38d3afe7478069d6d805` |
| `uz801-v3-lk1st-msm8916-20260527.mbn` | UZ801 v3.0 lk1st 候选配置 | `9d34e54f449054e45bde860a4c1334c32dd4a83178d9d61ffdfb4f9b4d44ea5c` |
| `jz0145-v33-lk1st-msm8916-20260527.mbn` | JZ0145 v33 lk1st 候选配置 | `29a615f846534e33c82dfccb91ae3ea2c7419140a2fa1b836243572651665c45` |
| `uf896-lk1st-msm8916-20260527.mbn` | UF896 lk1st 候选配置 | `0f7360db3ece77cc7ccb77698de9f5822f06a8653256ab989bc1506f03a1cbd5` |

`manifest.psv` 记录每个产物对应的源码 commit、bundle DTB、compatible 字符串和说明。
