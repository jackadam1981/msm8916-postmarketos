# UFI003 备份清单（本机实测）

> 生成时间：2026-10-23
> 数据来源：直接扫描本机 `backup/` 与 `nv_backup/`，大小与 sha256 均为实测值。
> 用途：救砖时快速判断手上有哪些素材、哪个能用。

---

## 1. 结论

备份**齐全**，总量约 32 GB。六份原厂全盘镜像全部是**原厂 27 分区布局**
（boot 16 MiB，含 system / cache / recovery），没有任何一份是刷过 pmOS 的状态，
都可以直接用来救砖。

`backup/3.53G miko包_UFI003.bin.7z` 和 `backup/3.53G_miko_UFI001C.7z`
已用 `7z t` 完整校验，均为 `Everything is Ok`。

---

## 2. 原厂全盘镜像（6 份）

| 文件 | 大小 | sha256（前 16 位） | 说明 |
|---|---|---|---|
| `backup/full/ufi003-reference.bin` | 3,791,650,816 | `61d90a219032c635` | 比 eMMC 多 16,896 B |
| `backup/full/qrzl903-reference.bin` | 3,867,148,288 | — | QRZL903（同方案另一型号） |
| `backup/UFI003-1/EMMC_3.82.bin` | 3,791,633,920 | `7256660359b4aa58` | 3.82 GB 整盘读 |
| `backup/UFI003-01.bin` | 3,791,633,920 | `f3efcd979db66340` | 01 号机整盘 |
| `backup/3.53G_miko_UFI003.bin` | 3,791,633,920 | `dc7dee25b28e69a5` | MIKO 原厂包（UFI003） |
| `backup/3.53G_miko_UFI001C.bin` | 3,791,633,920 | `fb56e93e6ec7f0e3` | MIKO 原厂包（UFI001C） |

全部 6 份的 GPT 校验结果一致：

```
parts=27  boot=16MiB  system=True  cache=True  recovery=True
```

### 压缩副本（省空间用）

| 文件 | 压缩后 | 解压后 |
|---|---|---|
| `backup/3.53G miko包_UFI003.bin.7z` | 192,571,230 | 3,791,633,920 |
| `backup/3.53G_miko_UFI001C.7z` | 192,522,085 | 3,791,633,920 |
| `backup/MIKO-QRZL903-1.zip` | 261,967,261 | 3,876,091,392（2 个文件） |

原厂固件基本是零填充，压缩比约 20:1。**只保留 .7z 就能省下约 10 GB**，
需要时 `7z x` 还原成同尺寸的 .bin。

---

## 3. 分区级备份

### 3.1 `backup/UFI003-1/`（单分区镜像，7.3 GB）

| 文件 | 大小 | sha256（前 16 位） |
|---|---|---|
| `persist.img` | 33,554,432 | `83ee47245398adee` |
| `modemst1.img` | 1,572,864 | `8f5c25f58c675ce3` |
| `modemst2.img` | 1,572,864 | `a42da8bde2b41a6c` |
| `fsg.mbn` | 1,572,864 | `852491301d8798c6` |
| `fsc.mbn` | 1,024 | `8deb82a040a10092` |
| `gpt_main0.bin` | 17,408 | `d0a2e583c038ffb9` |
| `gpt_backup0.bin` | 16,896 | — |
| `system.img` | 838,860,800 | `976094b0ea83cd64` |
| `boot.img` | 16,777,216 | — |
| `emmc_appsboot.mbn` / `sbl1.mbn` / `tz.mbn` / `rpm.mbn` / `hyp.mbn` | 见目录 | 引导链原件 |
| `partition.xml` / `rawprogram0.xml` / `patch0.xml` | — | Firehose 描述文件 |

> `full_emmc.bin`（379,486,208 B）只有 380 MB，开头全是零，**不是完整整盘镜像**，
> 不要拿它当救砖源。

### 3.2 `backup/_unpacked/`（原厂分区集，6.1 GB）

三套完整 27 件分区镜像，每套约 2.1 GB：

- `3.53G_miko_UFI003/` —— MIKO UFI003 原厂包解出来的
- `3.53G_miko_UFI001C/` —— UFI001C 对照
- `UFI003-01/` —— 01 号机

### 3.3 `nv_backup/`（现场 NV，4 个文件）

| 文件 | 大小 | sha256（前 16 位） |
|---|---|---|
| `UFI003-02/modemst1.bin` | 1,572,864 | `42587a2ca1bdab14` |
| `UFI003-02/modemst2.bin` | 1,572,864 | `07ca9bbfbdab070d` |
| `UFI003-02/fsg.bin` | 1,572,864 | `f7e804a9c0855fb8` |
| `UFI003-02/fsc.bin` | 1,024 | `5f70bf18a0860070` |

> `fsc.bin` 的哈希是全零文件的哈希 —— 这个分区本来就是空的（没有
> factory-mode 标记），不是备份失败。
> `nv_backup/UFI003-01/` 是空目录。

### 3.4 `backup/device-2026-07-31/`（56 MB）

2026-08-01 从 02 号机逐分区读出来的现场状态，含 `persist.bin`
（sha256 前 16 位 `9c7beeaff69517e8`）、`modemst1/2`、`fsg`、`fsc`、
`aboot`、`boot`、`hyp`、`rpm`、`sbl1`、`sec`，以及 GPT 的四个分量
（`lba0_mbr` / `lba1_gpt_header` / `gpt_entries` / `gpt_backup_*`）。
救砖时想还原「刷机前那一刻」的 NV，用这套比用原厂包更准。

---

## 4. 注意：救砖指南里的路径已失效

`docs/ufi003/ufi003-1-edl-restore-guide.zh-CN.md` 的 §2 素材清单点了两个
**当前不存在**的文件：

| 指南里写的 | 现状 |
|---|---|
| `backup/UFI003-1/full_emmc_dump_old_gpt.bin`（3,791,650,816，`5871b5d6…`） | 不存在；全盘扫描也没有任何文件匹配 `5871b5d6` |
| `backup/UFI003-1/system_partition_factory.img`（838,860,800，`5fe1b218…`） | 不存在；同尺寸的 `system.img` 哈希是 `976094b0…` |

按现在的实测结果，能直接用的原厂全盘镜像是本文 §2 那 6 份中的任意一份，
它们都带原厂 27 分区 GPT。选哪份当「权威源」取决于要还原哪台机器的现场
NV —— 这一点需要人工确认，不要凭文件名猜。

---

## 5. 复现这份清单

```bash
# 大小
find backup -type f -size +3500M -printf "%s\t%p\n" | sort -rn

# 哈希
sha256sum backup/full/*.bin backup/UFI003-1/EMMC_3.82.bin backup/UFI003-01.bin

# 压缩包完整性
"/c/Program Files/7-Zip/7z.exe" t "backup/3.53G miko包_UFI003.bin.7z"

# GPT 布局（每个镜像 27 分区、boot 16 MiB 即原厂状态）
python - <<'PY'
import struct
f = open('backup/UFI003-01.bin','rb'); f.seek(512); h = f.read(92)
assert h[:8] == b'EFI PART'
el = struct.unpack_from('<Q', h, 72)[0]
num = struct.unpack_from('<I', h, 80)[0]
esz = struct.unpack_from('<I', h, 84)[0]
f.seek(el*512); raw = f.read(num*esz)
names = [raw[i*esz+56:i*esz+128].decode('utf-16-le').rstrip('\0')
         for i in range(num) if raw[i*esz:i*esz+16] != b'\0'*16]
print(len(names), names)
PY
```
