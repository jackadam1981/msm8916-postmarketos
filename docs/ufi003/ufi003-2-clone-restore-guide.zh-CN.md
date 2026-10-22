# UFI003-2 克隆恢复指南（整盘克隆 UFI003-1 → UFI003-2）

> 状态：流程文档（2026-08-04）
> 目标：UFI003-2 完全变成 UFI003-1 的状态（原厂 Android + ADB + RNDIS），同时保留独立 IMEI/MAC。
> 前提：UFI003-1 当前状态良好（原厂 Android，adb+rndis 正常）；已具备全盘快照。

> **⚠ 2026-10-23 更正：`full_emmc_dump_old_gpt.bin` 已不在磁盘上。**
> 现在可用的是 6 份原厂全盘镜像，清单见
> [`backup-inventory.zh-CN.md`](./backup-inventory.zh-CN.md) §2。
> 下文命令里的文件名按清单替换后再执行。

---

## 0. 结论

- **可行**：两台同型号 `UFI003_MB_V02`（MSM8916，eMMC 3.53GB），secureboot disabled，EDL 可全盘读写。
- **方式**：全盘克隆一份原厂全盘镜像（如 `backup/UFI003-01.bin`）→ UFI003-2。
- **身份独立**：克隆前先现场备份 UFI003-2 的 NV（modemst1/2、fsg、persist、fsc），
  克隆后回写其自身 NV → UFI003-2 保留独立 IMEI/RF/MAC，其余状态与 UFI003-1 完全一致。

---

## 1. 前置确认

| # | 检查项 | 方法 |
|---|--------|------|
| 1.1 | UFI003-2 能进 9008 EDL | 短接 / 按钮 → `printgpt` 识别 |
| 1.2 | UFI003-2 eMMC 扇区数一致 | `printgpt` 显示 7,405,568 扇区（3.53GB） |
| 1.3 | 镜像源就绪 | `backup/UFI003-1/full_emmc_dump_old_gpt.bin`（sha256 `5871b5d6...`） |
| 1.4 | UFI003-2 现状记录 | 当前启动出 diag（无 rndis），克隆后将被覆盖为 UFI003-1 状态 |

> ⚠️ **扇区数必须一致**（7,405,568），否则不能全盘 `ws`，会写穿或错位。

---

## 2. 执行流程

### Step A — 现场备份 UFI003-2 NV（身份源，不可跳）

> 备份到独立目录 `backup/UFI003-2/nv_现场_<日期>/`。

```powershell
python edl.py r modemst1 backup\UFI003-2\nv_现场_<日期>\modemst1.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r modemst2 backup\UFI003-2\nv_现场_<日期>\modemst2.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r fsg      backup\UFI003-2\nv_现场_<日期>\fsg.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r fsc      backup\UFI003-2\nv_现场_<日期>\fsc.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py r persist  backup\UFI003-2\nv_现场_<日期>\persist.bin  --loader="<peek>" --memory=eMMC --skipstorageinit
```

✅ 验证：读回 sha256 记录；`persist` 解包核对 WiFi/BT MAC 为 UFI003-2 本机值。

### Step B — 备份 UFI003-2 原 GPT + 引导链（兜底）
```powershell
python edl.py printgpt --loader="<peek>" --memory=eMMC --skipstorageinit   # 留存文字 + 扇区数确认
python edl.py rs 0 34 backup\UFI003-2\gpt_原厂_<日期>.bin --loader="<peek>" --memory=eMMC --skipstorageinit
```

### Step C — 全盘克隆（写 UFI003-1 镜像到 UFI003-2）
```powershell
python edl.py ws 0 backup\UFI003-1\full_emmc_dump_old_gpt.bin --loader="<peek>" --memory=eMMC --skipstorageinit
```
> 耗时约 4–11 分钟（6–15MB/s × 3.79GB）。

✅ 验证：读回全盘比对
```powershell
python edl.py rs 0 7405568 verify_full.bin --loader="<peek>" --memory=eMMC --skipstorageinit
Get-FileHash verify_full.bin -Algorithm SHA256   # 期望 = 5871b5d6...
```

### Step D — 回写 UFI003-2 自身 NV（恢复独立身份）
```powershell
python edl.py w modemst1 backup\UFI003-2\nv_现场_<日期>\modemst1.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py w modemst2 backup\UFI003-2\nv_现场_<日期>\modemst2.bin --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py w fsg      backup\UFI003-2\nv_现场_<日期>\fsg.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py w fsc      backup\UFI003-2\nv_现场_<日期>\fsc.bin      --loader="<peek>" --memory=eMMC --skipstorageinit
python edl.py w persist  backup\UFI003-2\nv_现场_<日期>\persist.bin  --loader="<peek>" --memory=eMMC --skipstorageinit
```
✅ 验证：读回 sha256 与 Step A 一致。

### Step E — 上电验证
断电 → 解除短接 → 重新上电。

| 验证项 | 期望 |
|--------|------|
| USB 枚举 | 原厂复合设备（diag/serial/adb） |
| ADB | `adb devices` 显示 device |
| RNDIS | 主机出现 RNDIS 网卡，`ping 172.16.42.1` <1ms |
| IMEI | 查 UFI003-2 本机 IMEI（非 UFI003-1 值） |
| WiFi/BT MAC | persist 中为 UFI003-2 原值 |

---

## 3. 注意事项

1. **身份与功能可分离**：全盘克隆负责"功能状态"（build.prop rndis 配置、系统），
   NV 回写负责"身份"（IMEI/MAC/RF）。两者分开操作，互不干扰。
2. **不要跳过 Step A**：若克隆后才发现 UFI003-2 自身 NV 没备份，将无法恢复独立 IMEI/MAC。
3. **克隆后 IMEI 重复风险**：若跳过 Step D，UFI003-2 将使用 UFI003-1 的 IMEI/MAC，
   两台设备同时在线可能被运营商判重。
4. **扇区数校验**：UFI003-2 `printgpt` 必须为 7,405,568 扇区；否则中止并改用分区级克隆
   （见 `docs/ufi003/ufi003-1-edl-restore-guide.zh-CN.md` §4 方法 B）。
5. **改串工具**：如需额外改 IMEI，可在克隆恢复后用星辰SVIP/`am broadcast -a elink.action.limitSpeed --es imei`（见 `docs/ufi003/build.prop-改机笔记.md`）。

---

## 4. 与救砖/移植文档的关系

| 文档 | 用途 |
|------|------|
| `ufi003-1-edl-restore-guide.zh-CN.md` | 救砖（恢复单台原厂 Android） |
| 本文档 | 克隆（UFI003-1 状态复制到 UFI003-2） |
| `ufi003-1-pmos-porting-plan.zh-CN.md` | 后续 pmOS 移植（独立于本次克隆） |

*素材已 2026-08-04 核对。执行前确认 UFI003-2 已在 EDL 且扇区数匹配。*
