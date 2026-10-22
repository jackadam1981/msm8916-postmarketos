# 设备树进内核包（B 方案）落地记录

日期：2026-10-19
前置：`docs/ufi003-device-tree-sources.zh-CN.md`（设备树来源调研）

---

## 1. 做了什么

把 UFI003 的设备树从"仓库里一个 51 KB、源码丢失的二进制"改成"内核包里 106 行可审阅的 dts"。

| 位置 | 变化 |
|---|---|
| `config/kernel-testing/linux-postmarketos-qcom-msm8916/` | **新增**。内核包 overlay：`APKBUILD` + `0002-...patch` |
| `tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts` | **新增**。板级 dts 源（补丁的唯一真源） |
| `config/device-testing/device-410stick-ufi003-mb-v02/` | 删掉 `.dtb`，`source=` 只剩 `deviceinfo`，`pkgrel` 0 → 1 |
| `.github/workflows/pmos-build.yml` | 加内核包 overlay 步骤 + 显式编译内核 + 校验 apk 里有我们的 dtb；超时 120 → 300 分钟 |
| `.gitattributes` | `APKBUILD` / `deviceinfo` / `*.patch` / `*.dts` / `*.dtsi` 强制 LF |
| `scripts/pmaports/gen-kernel-dts-patch.py` | **新增**。从 dts 源生成补丁（不手写 diff） |
| `scripts/pmaports/sync-kernel-apkbuild.py` | **新增**。内核升级时从上游拉 APKBUILD 重新叠加 |
| `tools/dtb/dtb_dump.py` | **新增**。无依赖的 DTB 解析/比对工具（本地没有 dtc） |

## 2. 为什么 dtb 会从内核包里被找到

boot-deploy 的 `find_dtb()`（`postmarketOS/boot-deploy`，`main`，第 1416-1449 行）：

```sh
	# Alpine and modern pmOS dtb paths
	_dtb="$(find /boot -path "/boot/dtbs*/$_filename.dtb")"
	...
	# Legacy postmarketOS dtb path (for backwards compatibility)
	if [ -e "/usr/share/dtb/$_filename.dtb" ] && [ "$_dtb_found" = "false" ]; then
```

`/boot/dtbs*` **优先于** `/usr/share/dtb`。内核包 `dtbs_install` 把 dtb 装到
`/boot/dtbs/qcom/`，`deviceinfo_dtb="qcom/msm8916-zhihe-ufi003-mb-v02"` 拼出的正是
`/boot/dtbs/qcom/msm8916-zhihe-ufi003-mb-v02.dtb`。所以只要内核包里有这个文件，
设备包就不需要再装任何 dtb。

## 3. 补丁怎么打进去

pmaports 的 `linux-postmarketos-qcom-msm8916` 在 **`device/testing/`**（不是
`device/community/`，之前按 community 找全是 404）。6.12.1 版本的 `source=` 是：

```
$pkgname-$_tag.tar.gz::$url/archive/$_tag.tar.gz
config-$_flavor.aarch64
config-$_flavor.armv7
0001-kbuild-Add-fno-builtin-wcslen.patch
```

我们的 overlay 只做三件事（全部由 `sync-kernel-apkbuild.py` 生成，不手改）：

1. `source=` 末尾加 `0002-arm64-dts-qcom-msm8916-add-zhihe-ufi003-mb-v02.patch`
2. `sha512sums=` 末尾加它的 sha512
3. `pkgrel` 从上游 7 改成 8 —— 必须比二进制仓库的 `6.12.1-r7` 大，否则
   pmbootstrap 会直接装仓库里的 apk，我们的 dtb 根本不会编出来

`prepare()` 里 `default_prepare` 会自动 `patch -p1`，不需要改 `prepare()`。

补丁本身由 `gen-kernel-dts-patch.py` 从两个真实文件 diff 出来：

- 新文件 `arch/arm64/boot/dts/qcom/msm8916-zhihe-ufi003-mb-v02.dts`
- `arch/arm64/boot/dts/qcom/Makefile` 在 ufi001c 那行后面插一行 `dtb-... +=`

已用 `patch -p1 --dry-run` 和实打校验过：两个文件都干净应用，产物与
`tools/dtb/` 下的源 **逐字节一致**，Makefile 新行落在第 68 行。

## 4. 新旧 dtb 到底差在哪

用 `tools/dtb/dtb_dump.py diff` 比对了：

- A = 现在能开机的 51 KB 二进制
- B = pmOS 仓库 `linux-postmarketos-qcom-msm8916-6.12.1-r7.apk` 里的官方
  `msm8916-thwc-ufi001c.dtb`（50428 B）

结果：**448 vs 443 个节点，19 处属性差异**。差异几乎全是"内核版本漂移"，
不是板级差异：

| 节点 | A（在用的） | B（6.12 官方） | 结论 |
|---|---|---|---|
| `/` model / compatible | UFI003 / zhihe | ufi-001c / thwc | 预期差异，按 UFI003 写 |
| `/memory@80000000` reg | `0x20000000`（512 MiB） | `0x0`（等 bootloader 填） | **保留 512 MiB**，见 §5 |
| `/soc@0/remoteproc@4080000` | `cx/mx/pll-supply` + 5 个 `regulator-*` 节点 | `power-domains` + `power-domain-names` | 跟 6.12：驱动已改用 power domain |
| 同上 reg 第二段 | `0x100` | `0x40` | 跟 6.12 |
| `/soc@0/mmc@7824900` | 无 `vmmc/vqmmc-supply` | 有 | 跟 6.12 |
| `/soc@0/usb@78d9000` | `dr_mode="peripheral"`，无 `usb-role-switch` | `dr_mode="otg"` + `usb-role-switch` | **保留 peripheral**，见 §5 |
| `/soc@0/usb@78d9000/ulpi/phy` | `v1p8/v3p3-supply` = 0xa0/0xa1 | 0x60/0x5b | 跟着 regulator 改动走 |
| `/soc@0/video-codec@1d00000` | `disabled` | `okay` | **保留 disabled**，见 §5 |
| `/soc@0/remoteproc@4080000/bam-dmux` | `qcom,netdev-channel-mask = <1>` | 无 | 丢弃：6.12 的 `qcom,bam-dmux.yaml` 里**没有**这个属性，是下游残留 |
| `/` | `qcom,msm-id`、`qcom,board-id` | 无 | 丢弃：只有 lk2nd 选 dtb 才用，我们走 lk1st + append_dtb |

顺带一个结论：A 的 remoteproc 还是老的 `regulator-*` 绑定，而设备跑的是 6.12.1，
所以**当前 mpss（调制解调器）很可能根本没 probe 成功**。换成内核编出来的 dtb 顺带修掉这个。

## 5. 三处刻意偏离上游的地方

写进 dts 注释里了，这里展开：

**① memory 固定 512 MiB。** 上游 42 个 msm8916 dtb 全部是 `0x0` 等 bootloader 填
（我用 `dtb_dump.py` 扫了整个 apk 验证）。但 A 是硬编码 512 MiB 的，而 A 是唯一
验证过能开机的。lk1st 理论上会 patch 内存节点，但没法在设备离线时验证，所以选择
"即使 bootloader 不填也能开机"的那条路。512 MiB 与 `/proc/meminfo`、原厂 model
字符串（`MSM 8916 512MB MTP`）一致。若将来出现 256 MiB 变种，删掉这个 override。

**② USB 强制 peripheral。** 这是根插在电脑上的棒子，永远是 device。主线的
`usb-role-switch` + `extcon = <&pm8916_usbin>` 要靠 VBUS/ID 检测决定角色；一旦检测
不到就停在 otg、gadget 不注册、RNDIS 直接没了。A 用的就是 peripheral，沿用。

**③ venus 保持 disabled。** 这族棒子的 venus 已知不能用（OpenStick README 明说），
设备又没有屏幕。开了只会拖慢启动并刷一堆固件加载失败。

## 6. 怎么重新生成

改了 dts 之后：

```sh
python scripts/pmaports/gen-kernel-dts-patch.py   # 重新出 patch + 打印新 sha512
python scripts/pmaports/sync-kernel-apkbuild.py   # 重新出 APKBUILD（含新 sha512）
```

pmaports 升级内核之后：只跑第二条。CI 会比对 `pkgver`，不一致时打 `::warning::`
提示该跑了。

## 7. 验证状态

| 项 | 状态 |
|---|---|
| 补丁能干净应用 | ✅ `patch -p1` 实打通过 |
| 补丁产物与 dts 源一致 | ✅ `diff -q` 通过 |
| APKBUILD sha512 正确 | ✅ 脚本内计算，与 `sha512sum` 一致 |
| 工作流 YAML 合法 | ✅ `yaml.safe_load` 全部通过 |
| **dts 能编译** | ❌ **未验证**。本地没有 dtc（无 gcc/clang，WSL 被安全策略禁），只能靠 CI |
| **编出来的 dtb 能开机** | ❌ **未验证**。设备当前离线（`192.168.100.1` ping 不通） |

CI 里加了两道闸，编译不过或 dtb 没进 apk 都会在 `pmbootstrap build` 那步直接失败，
不会产出一个"看起来正常但没 dtb"的镜像。

## 8. 上机测试清单（设备回来后）

1. 刷入新 boot.img，串口看 `Linux version` 和 `Memory: ... 512MB`
2. `ls /boot/dtbs/qcom/ | grep zhihe` —— 确认 dtb 来自内核包
3. `cat /proc/device-tree/model` —— 应为 `UFI003_MB_V02 4G Modem Stick`
4. `lsusb` / Windows 侧确认 RNDIS 网卡出现，`ping 192.168.100.1`
5. `dmesg | grep -i remoteproc` —— 看 mpss 是否这次真的起来了
6. `systemctl --failed`

## 9. 回滚

设备包恢复旧 dtb：

```sh
git show f55e421:config/device-testing/device-410stick-ufi003-mb-v02/msm8916-zhihe-ufi003-mb-v02.dtb \
  > config/device-testing/device-410stick-ufi003-mb-v02/msm8916-zhihe-ufi003-mb-v02.dtb
```

再把 `source=` / `package()` / `sha512sums=` 加回去（同 commit 里的旧版 APKBUILD 可直接取）。
`/usr/share/dtb/` 是 boot-deploy 的第二顺位，但**只要内核包里还有同名 dtb，它仍然优先** ——
真要回滚必须同时把 `config/kernel-testing/` 整个删掉，否则 `/boot/dtbs` 里的新 dtb 照样生效。
