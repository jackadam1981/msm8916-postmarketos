# MSM8916 PostmarketOS / 标准 Linux 工作区概述

> 由 OpenCode 助手基于当前工作区实际结构生成 — 2026-07-21

## 1. 项目定位

本仓库是 **MSM8916（UFI003‑02 等 4G 棒）** 的 postmarketOS / 标准 Linux 移植与低层实验工作台。

- **主实验样本**：UFI003-02（`UFI003_MB_V02`）
- **产品路线**：`PBL → SBL1 (HandsomeHacker 定制) → TZ (DB410c) → HYP (qhypstub) → lk1st → Linux`
- **当前基线**：非 radio 基线已成立（eMMC、RNDIS、SSH、OpenRC、LED、input）；Radio 仍 blocked（Modem 未驱动）。**TF-A BL31 路线已废弃**（2026-07），当前为 v2 重新分区 + DB410c 引导链方案。详见 [docs/ufi003/edl-flash-plan.zh-CN.md](docs/ufi003/edl-flash-plan.zh-CN.md)
- **RNDIS LAN（2026-10 实测通过）**：Windows 插上即自动加载 `usb8023.sys`（"Remote NDIS Compatible Device"），LAN `192.168.100.1/24` + DHCP + NAT，主机可经 4G 出网并用 `ssh pmos@192.168.100.1` 管理。实现见 `scripts/device/usb-lan.sh`，验证记录见 [docs/bringup/thwc-ufi001c/reports/rndis-lan.md](docs/bringup/thwc-ufi001c/reports/rndis-lan.md)
- **编译机**：`jack@192.168.2.18`（`/home/jack/work/msm8916-standard-linux`）

## 2. 仓库说明

| 项 | 值 |
|----|----|
| 远程 `github` | https://github.com/jackadam1981/msm8916-postmarketos.git |
| 远程 `origin` | https://gitlab.jackadam.top/k3s-master/msm8916-postmarketos.git |
| 子模块 | `external/msm8916-postmarketos`（指向同一 github 仓库 main 分支） |
| 默认分支 | main |

> 注意：当前工作区 Git 仓库本身就是 `jackadam1981/msm8916-postmarketos`。README 的部分文档链接（`docs/`、`devices/`）指向更完整的主项目仓库，在本工作区不存在；如需查阅，请到对应主项目仓库查看。

## 3. 顶层目录结构

```
D:\My_Project\Msm8916\
├── .github/workflows/        CI 工作流（kernel / boot / lk1st / mem-boot）
├── backup/full/               参考固件备份（aboot、ufi003、qrzl903）
├── external/                  子模块（msm8916-postmarketos）
├── logs/                      运行日志
├── OpenStick/                 上游 OpenStick 项目 README 参考
├── out/lk1st-msm8916/         编译产物（lk1st *.mbn）
├── patches/                   自定义补丁（lk2nd UART fastboot 检测）
├── release/base-flash/        刷写素材（gpt / aboot / zeros / sbc）
├── scripts/                   顶层构建脚本（build_kernel.sh 等）
│   └── scripts/               旧脚本（lk2nd 变体、rootfs）
├── tools/                     GPT 读取、flash 工具、分析脚本
│   ├── flash/                 mkbootimg / gen_initramfs / flash_aboot 等
│   └── tools/                 部署 / 捕获 / 分析脚本（deploy_t1*.sh 等）
│       └── com_log/           loki 日志查询/比对
├── .venv/                     本地 Python 虚拟环境（pyserial 等）
├── Dockerfile                 基础构建环境（Debian bookworm + 工具链 + pmbootstrap）
├── edl_config.json            EDL 9008 模式刷写配置
├── PARTITION_PLAN.md          分区迁移方案（保留 15 个 NV 分区 + 2 GiB pmos_rootfs 自动扩容）
├── README.md                  项目导航与当前状态
├── log.txt                    edl sahara 抓取日志
└── tmp_aboot.bin              临时 aboot 二进制
```

> `.agents/` 目录存在但为空。`docs/`、`devices/`、`images/` 在本工作区不存在（README 引用，见上方「仓库说明」）。

## 4. 关键文件速查

| 主题 | 路径 |
|------|------|
| 项目导航 / 当前状态 | `README.md` |
| 分区方案（NV 保留 + pmos_rootfs 扩容） | `PARTITION_PLAN.md` |
| 容器构建环境 | `Dockerfile` |
| EDL 9008 配置 | `edl_config.json` |
| lk2nd UART fastboot 检测补丁 | `patches/lk2nd-0001-uart-fastboot-detect.patch` |
| 内核构建脚本（本地） | `scripts/build_kernel.sh` |
| lk2nd 变体构建（编译机） | `scripts/scripts/build_lk2nd_variants.sh` |
| rootfs 构建 | `scripts/scripts/build_rootfs.sh` |

## 5. CI 工作流（.github/workflows/）

| 文件 | 用途 | 状态 |
|------|------|------|
| `build-kernel.yml` | 编译主线内核 + dtbs + modules | 已有提交记录 |
| `build-boot.yml` | 内核 + initramfs + `boot.img` | 已有提交记录 |
| `build-lk1st.yml` | 编译 lk1st 引导 | 已有提交记录 |
| `mem-boot.yml` | 内核 + 极简 initramfs + `mem_boot.img`（RAM 启动验证） | **当前存在缩进 Bug，脚本只跑到内核编译即结束，导致 artifact 未生成** |
| `mem-boot-trigger.yml` | mem-boot 的另一种触发变体 | 存在 |

## 6. 构建与刷写脚本分类

### 6.1 构建（build_*）
- `scripts/build_kernel.sh` — 顶层内核构建入口
- `scripts/scripts/build_kernel.sh` — 同功能旧脚本
- `scripts/scripts/build_rootfs.sh` — pmbootstrap rootfs 构建
- `scripts/scripts/build_lk2nd_variants.sh` — 多设备 lk2nd/lk1st 变体构建
- `tools/tools/build_remote_ufi003_dtb_*.sh` — 远程 DTB 构建 / 修复
- `tools/tools/build_qsee_aarch32_gateway_blob.sh` — QSEE aarch32 gateway blob 构建
- `tools/tools/build_ufi003_smem_marker_kmod.sh` — SMEM marker 内核模块构建

### 6.2 部署（deploy_*）
- `tools/tools/deploy_t1y*.sh` — T1Y 系列部署脚本（t1y → t1y13）
- `tools/tools/deploy_t1{x,w,v,u,t,s...}.sh` — T1 系列其他部署脚本
- `tools/tools/deploy_pmos_build_to_buildhost.sh` — 把 pmOS 构建产物推到编译机
- `tools/tools/deploy_pas_proxy_*_to_buildhost.sh` — TF-A PAS proxy 各阶段推到编译机
- `tools/tools/deploy_tfa_*_to_buildhost.sh` — TF-A T1 变体推到编译机
- `tools/tools/deploy_unattended_tfa_to_buildhost.sh` — 无人值守 TF-A 部署
- `tools/tools/deploy_overnight_t1qr.sh` — 夜间 T1QR 部署

### 6.3 捕获与采集（capture_* / collect_*）
- `capture_ufi003_*_uart_*.ps1` — UART 抓取（reboot / stock qsee edl reset / pas 等）
- `capture_early_gate_boot_uart.ps1` — 早期 gate boot UART
- `capture_coherency_gate1_local_uart.ps1` — coherency gate1 本机 UART
- `capture_paslite_uart_sync.ps1` — PASLite UART 同步
- `capture_re2_*.ps1` — RE2 探针 UART
- `collect_ufi003_android_*_baseline.sh` — Android 基线采集（root / mba）
- `collect_ufi003_post_mba_kernel_validate.sh` — post-MBA 内核校验
- `cleanup_ufi003_log_collect.sh` — 日志采集清理

### 6.4 分析（analyze_* / find_* / extract_* / compare_*）
- `analyze_qsee_scm_dispatch.py` / `analyze_qsee_arm32_scm_dispatch.py` — QSEE SCM 调度分析
- `find_qsee_thumb_callgraph.py` — QSEE thumb 调用图
- `find_qsee_scm_dispatch_candidates.py` — SCM dispatch 候选查找
- `find_qsee_legacy_scm_handler.py` / `find_qsee_arm_scm_dispatch.py` — legacy SCM handler
- `extract_qsee_elf_info.py` — QSEE ELF 信息
- `extract_qsee_companion_blob.py` — QSEE companion blob 提取
- `extract_qcom_ids.py` — 提取 qcom,msm-id / qcom,board-id
- `extract_bootimg.ps1` — boot.img 解包
- `compare_qsee_preserve_offset.py` — QSEE preserve offset 比对
- `create_bringup_case.py` — bring-up 用例生成

### 6.5 刷写与 EDL（flash_* / tools/flash/）
- `tools/flash/mkbootimg.py` — 自带 mkbootimg（Python 实现）
- `tools/flash/gen_initramfs.py` — initramfs 生成
- `tools/flash/flash_aboot_v2.py` — aboot 刷写
- `tools/flash/test_ep_read.py` / `tmp_read_dtb.py` — EDL 读取测试
- `tools/flash/` 下的 `Image`、`Image-dtb`、`build_boot.img`、`emmc_appsboot-test-signed.mbn`、`vmlinuz`、`*.dtb`、`initramfs/` — 本地刷写素材
- `tools/tools/flash_ufi003_v2_edl.ps1` — v2 方案 EDL 批量刷写（GPT + 引导链 + NV + 系统）

### 6.6 源码应用（apply_*）
- `apply_tfa_pas_proxy_{31,32,33}_sources.sh` — TF-A PAS proxy 各版本源码应用
- `apply_tfa_companion_stage0{b,c,c_plus}_sources.sh` — TF-A companion 各 stage 源码应用
- `apply_uboot_qsee_companion_sources.sh` — U-Boot QSEE companion 源码应用
- `apply_ufi003_extlinux_dload_cmdline.sh` — extlinux download cmdline 应用

### 6.7 其他
- `tools/read_gpt.py` / `read_gpt_more.py` — GPT 表读取
- `tools/tools/admin_refresh_ufi003_rndis.ps1` — 管理员刷新 RNDIS（Windows）
- `tools/tools/fetch_pmos_build_artifacts.sh` — 拉 pmOS 构建制品
- `tools/tools/fetch_ufi003_q6v5_mba_debug_kernel.sh` — 拉 Q6V5 MBA debug 内核
- `tools/tools/com_log/{loki_query.json,show_loki.py,cmp_aboot.py,monitor_*.log}` — loki 日志系统对接

## 7. 备份与产物

### 7.1 backup/full/
- `ufi003-reference.bin` — UFI003 参考全量固件
- `qrzl903-reference.bin` — QRZL903 参考固件
- `aboot_reference.bin` — aboot 参考镜像

### 7.2 release/base-flash/
- `gpt_main0.bin` / `gpt_backup0.bin` / `gpt_both0.bin` — GPT 主/备/合并表
- `aboot.bin` — aboot 镜像
- `sbc_1.0_8016.bin` — SBC 镜像
- `zeros_1sector.bin` / `zeros_33sectors.bin` — 填充数据

### 7.3 out/lk1st-msm8916/
- `lk1st-msm8916.mbn` — lk1st 镜像
- `lk1st-msm8916-signed.mbn` — 签名版
- `emmc_appsboot-test-signed.mbn` — 测试签名 aboot

## 8. 子模块（external/msm8916-postmarketos）

- 指向同一 GitHub 仓库 `jackadam1981/msm8916-postmarketos` 的 `main` 分支
- 当前检出 commit：`a2105caa121a169d626107d771c1a39d7d40758e`
- 主要用于 CI 工作流集中维护（`mem-boot.yml` 等的「权威副本」）

## 9. OpenStick 项目参考（OpenStick/）

上游 OpenStick 项目 README，记录 msm8916 4G 网卡逆向 / 主线移植进度：
- 完成 msm8916-mainline 部分特性向 5.10 稳定内核移植
- 完成 HandsomeMod（openwrt）移植与 pmOS 运行
- Modem 在 HandsomeMod 中已驱动
- 未完成：视频编码器、部分 WiFi 型号切卡逻辑

## 10. 健康检查（见 README）

```bash
python3 -m compileall tools
python3 tools/lib/validate_device_metadata.py devices/openstick
```
> 注意 `tools/lib/` 与 `devices/openstick` 在本工作区不存在，需到主项目仓库执行。

Windows：`powershell -File tools/lib/ufi003_health_check.ps1`

## 11. 当前已知问题

| # | 问题 | 位置 | 严重度 |
|---|------|------|--------|
| 1 | ~~`mem-boot.yml` YAML 缩进不一致导致脚本只跑到内核编译即结束~~ **已修复**（heredoc 改 `printf`，run 39037146491 成功产出 13 MB `mem_boot.img`） | `.github/workflows/mem-boot.yml` | ~~高~~ 已关闭 |
| 2 | GitHub Actions 仍用 Node 20（已 deprecated，被强制 Node 24） | 多个 workflow 的 `actions/*@v4` | 中 |
| 3 | README 引用的 `docs/`、`devices/`、`tools/lib/` 在本工作区不存在 | `README.md` | 低（属另一主项目仓库） |
| 4 | `tools/lib/validate_device_metadata.py` 健康检查命令无法在本工作区运行 | `README.md` | 低 |

> 真机验证结果（含 `wlan0` 排查）见 `docs/bringup/thwc-ufi001c/reports/verification-report.md`。
> 结论：启动链、4G、USB 共享、WiFi 驱动栈均正常，零失败服务。
| 5 | 子模块与主仓库指向同一远程，无独立「外部上游」隔离 | `external/msm8916-postmarketos` | 低（设计如此） |

## 12. 典型工作流

### 12.1 本地构建（Dockerfile 容器）
1. `docker build .`（基于 `Dockerfile` 生成 `jackadam/pmos_build` 镜像）
2. 容器内执行 `scripts/build_kernel.sh` → 产物到 `/build/out/`
3. 可选：`scripts/scripts/build_rootfs.sh` 生成 pmOS rootfs

### 12.2 GitHub Actions 触发
```bash
# 触发 mem-boot（RAM 启动验证，当前有 Bug）
gh workflow run mem-boot.yml --repo jackadam1981/msm8916-postmarketos

# 触发其他 workflow
gh workflow run build-kernel.yml --repo jackadam1981/msm8916-postmarketos
gh workflow run build-boot.yml   --repo jackadam1981/msm8916-postmarketos
gh workflow run build-lk1st.yml  --repo jackadam1981/msm8916-postmarketos
```

### 12.3 EDL 刷写（9008 模式）
1. 设备进 EDL（隐藏按钮或 `fastboot oem edl`）
2. 用 `edl` 工具按 `edl_config.json` 备份/刷写
3. 参见 `PARTITION_PLAN.md` 第 4、5、6 节的备份/生成 GPT/刷 pmOS 流程
4. `tools/flash/` 提供 aboot 等细分刷写；`tools/tools/` 下有 v2 方案 EDL 批量脚本

### 12.4 UART 抓取与日志
- `tools/tools/capture_*_uart*.ps1` — 各阶段 UART 抓取
- `tools/tools/com_log/` — 通过 loki 查询/比对日志

---

*本概述依据当前工作区实际文件生成，并非修改任何源码。如需更新或补充，请直接编辑 `PROJECT_OVERVIEW.md`。*

