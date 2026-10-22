# 外部参考对照：Handsome OpenStick 逆向工程文章

## 来源

《我的4g网卡运行着GNU/Linux —— 某4g无线网卡的逆向工程与主线Linux移植（一）》
<https://blog.csdn.net/github_38345754/article/details/121462292>
发布于 2021-11-25。

作者对一块 MSM8916 4G 上网棒做了和我们同样的事：EDL 导出 eMMC、从 Android
boot.img 反编译设备树、移植 lk2nd、跑主线内核。它的价值在于**提供了 LED 的语义**
—— 哪个 GPIO 对应哪个功能指示灯，这是二进制里读不出来的。

## 身份确认：和我们这台是同一套参考设计

| 字段 | 文章 | 我们从固件提取的 vendor dtb |
|---|---|---|
| `model` | `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` | 同 |
| `qcom,board-id` | `<0x08 0x100>` | `<0x08 0x100>` |
| `qcom,msm-id` | `<0xce 0xf8 0xf9 0xfa>` | `<0xce 0xf8 0xf9 0xfa>` |

三项全同。注意这是高通的**通用 MTP 桶**，多个品牌的 8916 上网棒都会落在同一个
board-id 上，所以「同一参考设计」不等于「同一块 PCB」。凡有冲突，以我们从**本机固件**
提取的 vendor dtb 为准，文章只作交叉验证。

## 文章给出的 LED 定义（原文）

```c
gpio-leds {
	compatible = "gpio-leds";
	pinctrl-names = "default";
	pinctrl-0 = <0xec>;

	WIFI_S  { gpios = <0x4f 0x14 0x00>; label = "WIFI_S";  default-state = "off"; };
	4G_L2   { gpios = <0x4f 0x15 0x00>; label = "4G_L2";   default-state = "off"; };
	4G_L3   { gpios = <0x4f 0x44 0x00>; label = "4G_L3";   default-state = "off"; };
	4G_S    { gpios = <0x4f 0x16 0x00>; label = "4G_S";    default-state = "off"; };
	SIM_SEL { gpios = <0x4f 0x02 0x00>; label = "SIM_SEL"; default-state = "on";  };
	sim_en  { gpios = <0x4f 0x01 0x00>; label = "SIM_EN";  default-state = "off"; };
	FTM_ST  { gpios = <0x4f 0x24 0x00>; label = "FTM_ST";  default-state = "keep"; };
};
```

`0x4f` 是 tlmm 的 phandle，后一个 cell 是 GPIO 号。

## 与我们 vendor dtb 的逐项对照

| 节点 | GPIO | 文章 | 我们的 vendor dtb | 一致 |
|---|---:|---|---|---|
| `WIFI_S` | 20 | `off` | `off` | ✓ |
| `4G_L2` | 21 | `off` | `off` | ✓ |
| `4G_L3` | **68** | `off` | `off` | ✓ |
| `4G_S` | 22 | `off` | `off` | ✓ |
| `SIM_SEL` | 2 | **`on`** | **`off`** | ✗ |
| `sim_en` | 1 | `off` | `off` | ✓ |
| `ESIM_SEL` | 0 | 未提及 | `on` | — |
| `ESIM2_SEL` | 3 | 未提及 | `off` | — |
| `FTM_ST` | 36 | `keep` | `keep` | ✓ |

唯一的冲突是 `SIM_SEL` 的 `default-state`：文章写 `on`，我们的固件写 `off`。
我们的固件还多出 `ESIM_SEL`（`on`）和 `ESIM2_SEL`（`off`）两个节点。

两边的**默认选中项**其实是一致的，只是表达方式不同：

```
文章:      SIM_SEL=on  →  选外部 SIM 槽
我们的:    SIM_SEL=off + ESIM_SEL=on  →  也选外部 SIM 槽
```

因为 gpio0 在这里是 `ESIM_SEL`（低有效），拉高表示"不用 eSIM"，等价于选外部槽。
我们 dts 里 `gpio0` 配 `output-low`（选外部槽）走的也是这条路。

## pinctrl 范围：gpio68 不在里面

我们的 vendor dtb 里，`gpio_led_pins` 只配了 **8 个引脚**：

```c
qcom,pins = <0xe2 0x0 0xe2 0x1 0xe2 0x2 0xe2 0x3
             0xe2 0x14 0xe2 0x15 0xe2 0x16 0xe2 0x24>;
qcom,num-grp-pins = <0x8>;
```

也就是 GPIO **0, 1, 2, 3, 20, 21, 22, 36** —— 有 `4G_L3` 的 gpio68 的 LED 节点，
但**没有**把 gpio68 配进 pinctrl 组。

含义有两种可能，需要实物确认：

1. gpio68 上确实有第 4 颗灯，但 Android 从没点亮过它（pinctrl 没配，默认态是
   复位后的输入），所以 vendor 树里这条定义是残留；
2. gpio68 是这颗灯的默认配置（不需要显式 pinctrl），Android 通过 LED 子系统
   单独控制。

## 对我们 dts 的影响

现在的 `tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts` 把三颗灯当 RGB 处理：

```dts
&led_b { gpios = <&tlmm 20 GPIO_ACTIVE_HIGH>; };
&led_g { gpios = <&tlmm 21 GPIO_ACTIVE_HIGH>; };
&led_r { gpios = <&tlmm 22 GPIO_ACTIVE_HIGH>; };
```

GPIO 号是对的，但**语义错了**。上游 `msm8916-ufi.dtsi` 自己就写明了这是回退值：

> Functions and default-states defined here are fallbacks.
> Feel free to override them if your board is different.

真实映射：

| 我们的 label | GPIO | 实际含义 |
|---|---:|---|
| `led_b` | 20 | `WIFI_S` —— WiFi 状态 |
| `led_g` | 21 | `4G_L2` —— 4G 信号 2 档 |
| `led_r` | 22 | `4G_S` —— 4G 状态 |
| （缺） | 68 | `4G_L3` —— 4G 信号 3 档 |

不是红绿蓝三色灯，是**四颗单色功能指示灯**。`4G_L2` / `4G_L3` 成对出现，
通常表示信号强度档位，所以 gpio68 存在的可能性不低。

**暂不改功能定义**：`led_b/g/r` 三个 label 已经被上游 dtsi 和用户空间脚本使用，
改名会连带影响 `/sys/class/leds` 下的名字。等确认实物灯数后再一并调整。

## 文章里其它可用的信息

### Secure boot 状态

```sh
$ edl secureboot
Sec_Boot0 PKHash-Index:0 OEM_PKHash: False Auth_Enabled: False
...
Secure boot disabled.
```

和我们的情况一致 —— 所以可以用测试密钥签名 lk1st（`qtestsign`），这条路是通的。

### 原厂 kernel cmdline

```
console=ttyHSL0,115200,n8 androidboot.console=ttyHSL0 androidboot.hardware=qcom
user_debug=31 msm_rtb.filter=0x237 ehci-hcd.park=3
androidboot.bootdevice=7824900.sdhci earlyprintk
```

两个可直接用的点：

- `console=ttyHSL0,115200` —— 原厂 console 走 `ttyHSL0`，和我们 debug UART 的
  判断一致（`blsp1_uart2`，物理地址 `0x78b0000`）
- `androidboot.bootdevice=7824900.sdhci` —— 印证 eMMC 控制器是 `7824900`，
  正是我们树里 `mmc@7824900` 那个节点

### boot.img 里的设备树数量

文章说 `BOARD_DT_SIZE 5240832`、解出「200 多个」设备树。我们实际扫出来是
**33 个，合计 5.1 MiB**，与 `BOARD_DT_SIZE` 吻合（5,240,832 B ≈ 5.0 MiB）。
所以 33 个是全的，「200 多个」应该是把 QCDT 条目和别的表混在一起数了。

### USB 主机模式需要改硬件

文章提到「实现 usb 的模式切换的硬件 mod，可以让这个网卡的 usb 工作在主机模式下」。

这印证了我们 dts 里 `dr_mode = "peripheral"` 的判断：原厂硬件就是固定 device 模式，
要做 USB host（接 U 盘、摄像头）必须动硬件，不是改设备树能解决的。
