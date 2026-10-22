# UFI003 设备树来源调研

日期：2026-10-19
目的：确认是否有现成的设备树源码可以替代当前那个 51 KB 的二进制 DTB

---

## 1. 结论

**有源码，但没有 UFI003 这个型号。** 不过实测 UFI003 的板级定义和 UFI001C **完全一致**，
所以可以直接复用 `msm8916-thwc-ufi001c.dts`，只改 `model` / `compatible` 两行。

这也是为什么仓库里那个 `msm8916-zhihe-ufi003-mb-v02.dtb`（51 KB）能工作 ——
它的字符串段里是：

```
UFI003_MB_V02 4G Modem Stick
zhihe,ufi003-mb-v02
```

**不是**原厂提取的（原厂 model 是 `Qualcomm Technologies, Inc. MSM 8916 512MB MTP`，
大小 144837 字节，SHA-256 `7D4A2B20...`，见 `ufi003-device-tree-evidence.zh-CN.md`）。

也就是说：**这个 dtb 是有人基于上游 dts 改出来编译的，只是源码没入库。**

## 2. 两个上游

### 2.1 postmarketOS 路线（当前项目在用）

仓库：`https://github.com/msm8916-mainline/linux`，分支 `msm8916/6.12`

`arch/arm64/boot/dts/qcom/` 下与这族棒子相关的只有三个文件：

| 文件 | 作用 |
|---|---|
| `msm8916-ufi.dtsi` | **公共部分**（147 行） |
| `msm8916-thwc-ufi001c.dts` | UFI001B / UFI001C（60 行） |
| `msm8916-thwc-uf896.dts` | UF896（36 行） |

**没有** ufi003 / uz801 / sp970 / zhihe。

### 2.2 Debian 路线（OpenStick）

仓库：`https://github.com/OpenStick/linux`，默认分支 `master`（最后推送 2023-07-15）
说明：`Linux mainline kernel fork for many Qualcomm MSM8916/APQ8016 devices`

| 文件 | 作用 |
|---|---|
| `msm8916-handsome-openstick-common.dtsi` | 公共部分（211 行） |
| `msm8916-handsome-openstick-ufi001b.dts` | UFI001B |
| `msm8916-handsome-openstick-ufi001c.dts` | UFI001C |
| `msm8916-handsome-openstick-uz801.dts` | UZ801 |
| `msm8916-handsome-openstick-sp970.dts` | SP970 |

**也没有** ufi003。

两者是同一批人不同时期的产物（`handsome,openstick` 这个 compatible 就出自 HandsomeYingyan）。
OpenStick 那套基于较老内核（用 `&msmgpio`、`blsp1_uart2`、`pronto`），
主线那套用新命名（`&tlmm`、`blsp_uart2`、`wcnss`）。**写新 dts 应该用主线那套。**

## 3. 板级差异实测：UFI003 vs UFI001C

把设备当前运行的设备树反编译出来（`dtc -I fs -O dts /sys/firmware/devicetree/base`），
逐项对比 `msm8916-thwc-ufi001c.dts`：

| 项 | UFI003（实测） | UFI001C（上游） | 一致 |
|---|---|---|---|
| 重启键 | `<&tlmm 0x25 0>` = **gpio37**，ACTIVE_HIGH | `<&tlmm 37 GPIO_ACTIVE_HIGH>` | ✅ |
| LED 绿 (wlan) | phandle 0x49, **0x15 = 21**, ACTIVE_HIGH | `<&tlmm 21>` | ✅ |
| LED 红 (power) | **0x16 = 22**, ACTIVE_HIGH, default on | `<&tlmm 22>` | ✅ |
| LED 蓝 (wan) | **0x14 = 20**, ACTIVE_HIGH | `<&tlmm 20>` | ✅ |
| LED pinctrl | `pins = "gpio20","gpio21","gpio22"` | 同 | ✅ |
| SIM sel | `gpio2` output-high | 同 | ✅ |
| SIM en | `gpio1` output-low | 同 | ✅ |
| eSIM sel | `gpio0`, `gpio3` output-low | 同 | ✅ |

**八项全一致。** 唯一的差别是 `model` 和 `compatible`。

## 4. 建议的落地方式

新增 `msm8916-zhihe-ufi003-mb-v02.dts`，内容基本是 ufi001c 的副本：

```dts
// SPDX-License-Identifier: GPL-2.0-only

/dts-v1/;

#include "msm8916-ufi.dtsi"

/ {
	model = "UFI003_MB_V02 4G Modem Stick";
	compatible = "zhihe,ufi003-mb-v02", "qcom,msm8916";
};

&button_restart {
	gpios = <&tlmm 37 GPIO_ACTIVE_HIGH>;
};

&led_b { gpios = <&tlmm 20 GPIO_ACTIVE_HIGH>; };
&led_g { gpios = <&tlmm 21 GPIO_ACTIVE_HIGH>; };
&led_r { gpios = <&tlmm 22 GPIO_ACTIVE_HIGH>; };

&mpss {
	pinctrl-0 = <&sim_ctrl_default>;
	pinctrl-names = "default";
};

&button_default { pins = "gpio37"; bias-pull-down; };
&gpio_leds_default { pins = "gpio20", "gpio21", "gpio22"; };

&tlmm {
	sim_ctrl_default: sim-ctrl-default-state {
		esim-sel-pins { pins = "gpio0", "gpio3"; function = "gpio";
			bias-disable; output-low; };
		sim-en-pins   { pins = "gpio1"; function = "gpio";
			bias-disable; output-low; };
		sim-sel-pins  { pins = "gpio2"; function = "gpio";
			bias-disable; output-high; };
	};
};
```

约 40 行，替代现在 51 KB 的不可维护二进制。

两条路径：

| 路径 | 做法 | 代价 |
|---|---|---|
| **A. 只换 DTB**（快） | 本地用 dtc 编译成 dtb，替换 `config/device-testing/.../msm8916-zhihe-ufi003-mb-v02.dtb` | 仍要提交二进制，但源码终于可读了 |
| **B. 进内核包**（正） | 把 dts 加进 `linux-postmarketos-qcom-msm8916` 的 pmaports 包 | 每次内核升级自动重编，但需要维护 pmaports 补丁 |

A 能立刻消除"源码丢失"的问题；B 才是长期方案，但要维护一个内核包补丁。

> **2026-10-19 更新：已按 B 落地。** 实际写入的 dts 比上面这份草案多三处刻意偏离
> （memory 固定 512 MiB、USB 强制 peripheral、venus 保持 disabled），理由见
> `docs/bringup/thwc-ufi001c/reports/device-tree-in-kernel.md` 第 5 节。
> 内核包实际在 pmaports 的 `device/testing/` 而不是 `device/community/`。

## 5. 未验证的部分

- 上面这份 dts 草案**没有编译过**，也没在真机上跑过。本地没有 dtc 和内核头文件
  （无 gcc/clang，WSL 被安全策略禁用），只能靠 CI 编译。
- `&gcc` 的 clocks 覆写、`mpss_mem` 的地址（`0x86800000 + 0x5500000`）来自 `ufi.dtsi`。
  **已用 `tools/dtb/dtb_dump.py` 比对确认**：在用 dtb 与 6.12 官方 ufi001c dtb 在这两个
  节点上完全一致，说明 ufi.dtsi 的值与能开机的配置相符。
- 视频编码（venus）在这族上已知有问题（OpenStick README 明确写了），不属于设备树范畴。
- 全部 19 处属性差异的逐条解释见
  `docs/bringup/thwc-ufi001c/reports/device-tree-in-kernel.md` 第 4 节。

## 6. 参考链接

- `https://github.com/msm8916-mainline/linux/blob/msm8916/6.12/arch/arm64/boot/dts/qcom/msm8916-ufi.dtsi`
- `https://github.com/msm8916-mainline/linux/blob/msm8916/6.12/arch/arm64/boot/dts/qcom/msm8916-thwc-ufi001c.dts`
- `https://github.com/OpenStick/linux/tree/master/arch/arm64/boot/dts/qcom`
- `https://github.com/OpenStick/OpenStick`（Debian 刷机包与 wiki）
