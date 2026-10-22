# UFI003-1 救砖指南：EDL 模式完全恢复 Android

> 状态：流程文档（2026-08-04）
> 适用：UFI003-1（`UFI003_MB_V02`，MSM8916，eMMC 7,405,568 扇区 = 3.53GB）
> 用途：无论设备被刷成 postmarketOS / 引导链损坏 / USB 全消失，均可经 9008 完全恢复原厂 Android。

> **⚠ 2026-10-23 更正：本文点名的两个文件已不在磁盘上。**
> `backup/UFI003-1/full_emmc_dump_old_gpt.bin` 和
> `backup/UFI003-1/system_partition_factory.img` 都不存在，全盘扫描也没有任何
> 文件匹配 `5871b5d6…`。现在可用的是 6 份原厂全盘镜像（都带原厂 27 分区 GPT，
> boot 16 MiB），清单见 [`backup-inventory.zh-CN.md`](./backup-inventory.zh-CN.md)。
> 下文命令里的文件名按清单替换后再执行。

---

## 0. 核心结论

- **恢复权威源 = 本机自身全盘快照**，实际文件见 `backup-inventory.zh-CN.md` §2
  （`backup/UFI003-01.bin`、`backup/UFI003-1/EMMC_3.82.bin`、
  `backup/full/ufi003-reference.bin` 等任选其一）。
- **推荐方法 A（全盘回写）**：一条 `ws` 写满整个 eMMC，恢复率 100%（含 GPT + 全部原厂分区 + 现场 NV + userdata）。
- **方法 B（分区级）**：只写关键分区，写量小、更可控，适合只想"救活"而非完整还原的场景。
- 前提：Secure boot disabled（HandsomeHacker 参考一已证），EDL 9008 可自由读写。

---

## 1. 前提与环境

| 项 | 值 |
|----|----|
| 设备模式 | 9008 EDL（背面按钮短接 / `fastboot oem edl`） |
| 主机 | Windows + venv |
| Python | `D:\My_Project\Msm8916\.venv\Scripts\python.exe` |
| edlclient | `.venv\Lib\site-packages\edlclient\edl.py`（Sahara/Firehose V3.62） |
| Peek loader | `C:\Users\jacka\AppData\Roaming\Python\Python312\site-packages\Loaders\lyf\007050e100000000_394a2e47cf830150_fhprg_peek.bin` |
| 通用参数 | `--loader="<peek>" --memory=eMMC --skipstorageinit` |

> Windows 下需先把 `...\libusb_package` 加入 PATH + `os.add_dll_directory()` 再 `import usb.core`（edlclient CLI 已内部处理）。

检查设备在 EDL：

```powershell
python edl.py printgpt --loader="<peek>" --memory=eMMC --skipstorageinit
# 期望输出 Mode detected: firehose + GPT 列表
```

---

## 2. 救砖素材清单（2026-10-23 重新核对）

| 素材 | 路径 | 大小 | sha256(前16) | 说明 |
|------|------|------|------|------|
| **本机全盘快照** | `backup/UFI003-01.bin` | 3,791,633,920 | `f3efcd979db66340` | **可用，原厂 27 分区 GPT** |
| 本机全盘快照（备份） | `backup/UFI003-1/EMMC_3.82.bin` | 3,791,633,920 | `7256660359b4aa58` | 同一布局，另一份 |
| 参考镜像 | `backup/full/ufi003-reference.bin` | 3,791,650,816 | `61d90a219032c635` | 比 eMMC 多 16,896 B |
| MIKO 原厂包 | `backup/3.53G_miko_UFI003.bin` | 3,791,633,920 | `dc7dee25b28e69a5` | 另有 .7z 压缩副本 |
| 原厂 GPT（设备当前） | `build/out/gpt_current_backup.bin` | 17,408 | `d0a2e583c038ffb9` | 与 08-03 实读一致 |
| 原厂 system 镜像 | `backup/UFI003-1/system.img` | 838,860,800 | `976094b0ea83cd64` | 与旧记录的 `5fe1b218…` 不同，回刷前先确认 |
| 原厂分区集 UFI003 | `backup/_unpacked/3.53G_miko_UFI003/*.img` | 全套 27 件 | 见 §5 表 | 含 boot/aboot/sbl1/tz/hyp/rpm |
| 原厂分区集 UFI001C | `backup/_unpacked/3.53G_miko_UFI001C/*.img` | 全套 27 件 | 见 §5 表 | 对照备份 |

> 完整清单（含 6 份全盘镜像的哈希与 GPT 校验）见
> [`backup-inventory.zh-CN.md`](./backup-inventory.zh-CN.md)。
> 注意 `backup/UFI003-1/full_emmc.bin` 只有 380 MB、开头全是零，**不是整盘镜像**。

---

## 3. 方法 A — 全盘回写（推荐，100% 恢复）

> 一次性把整个 eMMC 写成救砖快照。耗时：约 6–15MB/s × 3.79GB ≈ **4–11 分钟**。

```powershell
python edl.py ws 0 backup/UFI003-1/full_emmc_dump_old_gpt.bin `
  --loader="<peek>" --memory=eMMC --skipstorageinit
```

✅ 写入完成后立即读回验证（全盘，约 4–11 分钟）：

```powershell
python edl.py rs 0 7405568 verify_full.bin `
  --loader="<peek>" --memory=eMMC --skipstorageinit
```

```powershell
Get-FileHash verify_full.bin -Algorithm SHA256
# 期望 = 5871b5d67046f5be...（与 full_emmc_dump_old_gpt.bin 一致）
```

断电 → 解除短接 → 重新上电，原厂 Android 即恢复。

---

## 4. 方法 B — 分区级回写（最小干预）

> 仅重写「引导链 + 系统」关键分区，不动 NV（保留现场 IMEI/RF/MAC）与 userdata。
> 原厂分区起始 LBA（来自 08-03 实读 GPT）：

| 分区 | 起始 LBA | 扇区数 | 内容源 |
|------|---------|--------|--------|
| sbl1 | 262144 | 1024 | `_unpacked/3.53G_miko_UFI003/sbl1.img` |
| aboot | 264192 | 2048 | `_unpacked/3.53G_miko_UFI003/aboot.img` |
| rpm | 268288 | 1024 | `_unpacked/3.53G_miko_UFI003/rpm.img` |
| tz | 270336 | 1024 | `_unpacked/3.53G_miko_UFI003/tz.img` |
| hyp | 272384 | 1024 | `_unpacked/3.53G_miko_UFI003/hyp.img` |
| boot | 396384 | 32768 | `_unpacked/3.53G_miko_UFI003/boot.img` |
| system | 429152 | 1638400 | `backup/UFI003-1/system_partition_factory.img` |
| modemst1 | 276480 | 3072 | 建议保留现场 NV（可选回写） |
| modemst2 | 279552 | 3072 | 同上 |
| persist | 2067552 | 65536 | 同上 |
| fsg | 393280 | 3072 | 同上 |

刷写示例（引导链 + 系统，不动 NV）：

```powershell
python edl.py ws 262144 backup\_unpacked\3.53G_miko_UFI003\sbl1.img  --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 264192 backup\_unpacked\3.53G_miko_UFI003\aboot.img --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 268288 backup\_unpacked\3.53G_miko_UFI003\rpm.img   --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 270336 backup\_unpacked\3.53G_miko_UFI003\tz.img    --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 272384 backup\_unpacked\3.53G_miko_UFI003\hyp.img   --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 396384 backup\_unpacked\3.53G_miko_UFI003\boot.img  --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py ws 429152 backup\UFI003-1\system_partition_factory.img --loader="<peek>" --memory=eMMC --skipstorageinit
```

> 若 GPT 也被改过（如刷了 pmOS 15 分区表），需先回刷原厂 GPT：
> `python edl.py ws 0 build\out\gpt_current_backup.bin ...`

✅ 每步可选 `rs <lba> <n>` 读回比对 hash；系统分区读回验证流程见 `docs/ufi003/edl-flash-guide.zh-CN.md` §5。

---

## 5. 原厂分区集参考表（sha256 前 16）

> 两份解包目录内容几乎一致（bootloader 相同），差异仅在 modemst1/2、ssd、cache、userdata 等数据区。

| 分区 | UFI003 | UFI001C |
|------|--------|---------|
| sbl1 / sbl1bak | `25c52297...` | `25c52297...` |
| aboot | `0b7617b0...` | `0b7617b0...` |
| abootbak | `aeee076c...` | `aeee076c...` |
| rpm / rpmbak | `e1a66f69...` | `e1a66f69...` |
| tz / tzbak | `d3bc9ed2...` | `d3bc9ed2...` |
| hyp / hypbak | `d48bff77...` | `d48bff77...` |
| boot | `7f733f94...` | `7f733f94...` |
| system | `fc022ec3...` | `fc022ec3...` |
| modemst1 | `6d459d4e...` | `55822c9f...` |
| modemst2 | `07ca9bbb...` | `1d98d7e8...` |
| persist | `396a264a...` | `88888325...` |
| fsg | `f7e804a9...` | `f7e804a9...` |
| fsc | `5f70bf18...` | `5f70bf18...` |
| sec | `3b1cae78...` | `3b1cae78...` |

> bootloader 区（sbl1/aboot/rpm/tz/hyp/boot/system/fsg/fsc/sec）两套完全一致；
> **NV 数据区（modemst1/2、persist）不同**——恢复完整原厂状态时以本机现场备份为准（见 §6）。

---

## 6. NV 现场备份（IMEI / RF / MAC 权威源）

> 若方法 B 选择回写 NV，或需要先备份本机 NV，按 `docs/ufi003/edl-flash-plan.zh-CN.md` Step 1 执行。
> 简述：

```powershell
python edl.py r modemst1 backup\UFI003-1\nv_现场_<日期>\modemst1.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r modemst2 backup\UFI003-1\nv_现场_<日期>\modemst2.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r fsg      backup\UFI003-1\nv_现场_<日期>\fsg.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r fsc      backup\UFI003-1\nv_现场_<日期>\fsc.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r persist  backup\UFI003-1\nv_现场_<日期>\persist.bin  --loader="<peek>" --memory=eMMC --skipstorageinit
```

---

## 7. 注意事项

1. **先备份再救砖**：救砖素材已具备，但若设备曾有自定义改动，先做一次 `printgpt` + NV 读取留存。
2. **断电拔插**：每次 EDL 操作完成后必须断电 → 解除短接 → 重新上电，否则可能一直停在 9008。
3. **识别设备**：UFI003 与 QRZL903 分区布局不同，**不可互刷**（README 安全原则）。救砖只针对 UFI003-1。
4. **分区表必须匹配**：若当前 GPT 是 pmOS 15 分区表，回写方法 B 前**必须先回刷原厂 GPT**（`ws 0 gpt_current_backup.bin`），否则 LBA 对应错误。
5. **耗时**：全盘回写 4–11 分钟，分区级 1–2 分钟；期间不要拔 USB。

---

*素材已 2026-08-04 核对。恢复完成后按 `edl-flash-plan.zh-CN.md` Step 7 验证原厂 Android 枚举。*
