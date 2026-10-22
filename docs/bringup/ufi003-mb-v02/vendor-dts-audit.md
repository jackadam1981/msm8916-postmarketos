# UFI003_MB_V02 原厂设备树核对

日期：2026-10-21
目的：拿原厂 Android 固件里的设备树，逐项核对 `tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts`

---

## 1. 数据怎么来的

```
backup/UFI003-1/EMMC_3.82.bin        完整 eMMC dump，3,791,633,920 B
  └─ LBA 396,384 起 16 MiB           boot 分区，magic = ANDROID!
       └─ offset 6,649,856            QCDT 表，33 个 dtb
            └─ dtb-04                 qcom,board-id = <8 0x100>  ← 本机
```

选中依据：

| 属性 | 值 |
|---|---|
| `qcom,msm-id` | `<206 0>, <248 0>, <249 0>, <250 0>` |
| `qcom,board-id` | `<8 0x100>` |
| `model` | `Qualcomm Technologies, Inc. MSM 8916 512MB MTP` |
| `compatible` | `qcom,msm8916-mtp`, `qcom,msm8916`, `qcom,mtp` |
| 大小 | 144,551 B |

存档：

- `vendor-dtb-board8-subtype0x100.dtb` — 原厂 dtb 二进制，144,551 B
- `vendor-dts.dts` — **反编译出的 dts 源码**，6,947 行，由 `tools/dtb/dtb2dts.py` 生成
- `vendor-dtb-tree.txt`（`tools/dtb/dtb_dump.py dump` 输出，5,822 行）

> 本机没有 `dtc`（也没有 cpp / gcc），所以反编译用自己写的
> `tools/dtb/dtb2dts.py` 完成，不是 `dtc -I dtb -O dts`。
> 两者输出格式一致（字符串列表 / `<0x..>` 单元 / `[..]` 字节数组），
> 但 dtc 反编译时会用 `__symbols__` 恢复标签名，这个 dtb 里没有
> `__symbols__`，所以引用一律是数字 phandle，文件末尾附了
> phandle → 节点路径的对照表。
>
> 保真度校验：反编译结果 873 个节点、4,947 条属性，与二进制解析
> 结果**逐项一致**；括号配平；无属性被误判成字节数组。
> 丢失的是注释、`#include` 结构、标签名、宏 —— 这些本就不存在 dtb 里。

注意：原厂这份是**高通公版 MTP 树**，不是厂商为 UFI003 单独写的。板级信息散落在 `gpio-keys`、`gpio-leds`、`memory` 等节点里。

---

## 2. 一致的项

| 项 | 原厂 | 我们的 dts | |
|---|---|---|---|
| 内存 | `modem_adsp_region` = `0x86800000 + 0x5500000` | `&mpss_mem` 同值 | ✅ |
| 重启键 | gpio **37**, ACTIVE_HIGH | `&button_restart` gpio37 | ✅ |
| USB 模式 | `qcom,hsusb-otg-mode = 0x1`（peripheral） | `dr_mode = "peripheral"` | ✅ |
| eMMC | `sdhci@07824000` = okay | `&sdhc_1` okay | ✅ |
| SD 卡 | `sdhci@07864000` = disabled | 未启用 | ✅ |
| sim_en | gpio **1**, output-low | gpio1, output-low | ✅ |
| ESIM2_SEL | gpio **3**, output-low | gpio3, output-low | ✅ |
| 调试串口 | `blsp1_uart1`(78af000) + `blsp1_uart2`(78b0000) 都 okay | `blsp_uart2` okay | ⚠️ 见 §4 |

---

## 3. 差异项

### 3.1 SIM_SEL 电平相反（确凿，建议改）

原厂 `gpio_led_pins` 把 8 个脚统一配置为 `output-low`：

```
qcom,pins = <0 1 2 3 20 21 22 36>
led_off { drive-strength = <2>; bias-disable; output-low; }
```

其中 `SIM_SEL` = **gpio2**。

我们的 dts：

```dts
sim-sel-pins {
    pins = "gpio2";
    output-high;      /* ← 原厂是 output-low */
};
```

这一处是从 `msm8916-thwc-ufi001c.dts` 抄来的。UFI003 的原厂配置是低电平，
两者相反。如果这个脚是内置/外置 SIM 槽选择，电平反了会导致插卡不识别。

**改之前需要确认：当前插 SIM 卡能不能用？**

- 现在能用 → 说明硬件上高电平也是外置槽，改 low 反而会坏
- 现在不能用 → 大概率就是这里，改成 low 有依据

### 3.2 原厂有、我们没有的 GPIO

| 原厂 label | GPIO | 用途 | 我们 |
|---|---|---|---|
| `4G_L3` | **68** | 4G 指示灯 | 完全没有 |
| `FTM_ST` | **36** | 工厂测试状态 | 完全没有 |

gpio36 也在那 8 个 `output-low` 脚里，但它是产测脚，主线不需要驱动。
gpio68 不在 pinctrl 组里，原厂也没给它配 pinctrl。

### 3.3 LED 功能标签对不上

原厂三个 LED 的 label 是**功能名**，不是颜色：

| GPIO | 原厂 label | 我们的 dts |
|---|---|---|
| 20 | `WIFI_S` | `led_b`（蓝）→ `LED_FUNCTION_WAN` |
| 21 | `4G_L2` | `led_g`（绿）→ `LED_FUNCTION_WLAN` |
| 22 | `4G_S` | `led_r`（红）→ `LED_FUNCTION_POWER` |

也就是说，按原厂命名，**gpio20 是 WiFi 灯、gpio21/22 是 4G 灯**。
我们现在把 gpio20 标成 WAN、gpio21 标成 WLAN，功能是错位的。

但原厂只给了功能名，没给颜色。改标签前需要知道实物上这三个灯分别是什么颜色，
否则 `/sys/class/leds/` 下的名字会和实际观感对不上。

### 3.4 原厂定义了 ST7735S 128×128 SPI 屏

原厂 dtb 里有完整的 panel 定义：

```
qcom,mdss_spi_st7735s_128128_cmd
  qcom,mdss-spi-panel-width  = 0x1e0   (480)
  qcom,mdss-spi-panel-height = 0x356   (854)
  qcom,platform-reset-gpio   = <&tlmm 25 0>
  qcom,platform-spi-dc-gpio  = <&tlmm 23 0>
```

bootargs 里也指定了：`mdss_mdp.panel=1:spi:0:qcom,mdss_spi_st7735s_128128_cmd`

注意宽高写的是 480×854，但 panel 名字叫 128128 —— 厂商从别的 panel 抄过来只改了
初始化序列，尺寸没改。这类"名字对、参数没调"的情况，通常是参考设计的残留。

而且 `mdss_spi` 是**下游 Android 专有实现**，主线内核没有对应驱动
（主线只有 `mdss_dsi`）。所以即使硬件上真有屏，也不是改 dts 能解决的，需要写驱动。

**需要确认：设备正面有没有一块小屏幕？**

---

## 4. 一个容易踩的坑：console 口

| | 物理 UART | 设备名 |
|---|---|---|
| 原厂 Android | `78af000`（blsp1_uart1） | `ttyHSL0` |
| 我们（ufi.dtsi） | `78b0000`（blsp_uart2） | `ttyMSM0` |

不是同一个口。我们能收到日志，说明 78b0000 也引出了测试点；
但如果照着原厂维修手册去接 78af000，可能什么都看不到。

---

## 5. 现状：三条都已确认

| 问题 | 结论 | 处理 |
|---|---|---|
| SIM 卡能不能用 | 能用，插卡识别并注册 | `gpio2` 保持 `output-high`，**不要照 vendor 改成 low** |
| 设备有没有屏 | 没有 | ST7735S 不处理，`mdss_spi` 主线也无驱动 |
| LED 是 RGB 还是功能灯 | **功能灯**，四颗单色 | GPIO 号对，语义写进 dts 注释；`gpio68` 暂不加 |

### LED 的准确语义

vendor 树和一份外部拆解记录（`external-references.md`）互相印证：

| 我们 dts 里的 label | GPIO | 真实含义 |
|---|---:|---|
| `led_b` | 20 | `WIFI_S` — WiFi 状态 |
| `led_g` | 21 | `4G_L2` — 4G 信号 2 档 |
| `led_r` | 22 | `4G_S` — 4G 状态 |
| （未定义） | 68 | `4G_L3` — 4G 信号 3 档 |

上游 `msm8916-ufi.dtsi` 自己写了这些是回退值：
「Functions and default-states defined here are fallbacks. Feel free to
override them if your board is different.」所以 label 叫 `led-b/g/r` 只是
上游的占位命名，不影响功能。

`gpio68` 不加的理由：vendor 的 `gpio_led_pins` 只配了 GPIO 0-3、20-22、36
这 8 个脚，**不含 68**。也就是说第四颗灯在 vendor 树里有节点但从没被配置过，
实物是否焊了无法确认。

### 全树扫描

873 个节点的完整对照见 `vendor-vs-ours-audit.md`，由
`tools/dtb/dtb_audit.py` 生成。结论：**没有发现真正缺失的硬件**。

唯一未决项是音频 —— vendor 的 `sound` 节点驱动一个 GPIO 12 上的外部功放，
我们的树用的是 DB410c 的 `apq8016-sbc-sndcard`。上网棒大概率没有扬声器，
但没拆过，存疑。

---

## 6. 怎么重新生成反编译结果

```sh
# 从二进制还原成 dts
python tools/dtb/dtb2dts.py \
  docs/bringup/ufi003-mb-v02/vendor-dtb-board8-subtype0x100.dtb \
  -o docs/bringup/ufi003-mb-v02/vendor-dts.dts

# 两个 dtb 直接比结构（跳过文件头注释，只比节点和属性）
python tools/dtb/dtb2dts.py --diff a.dtb b.dtb
```

`--diff` 比的是反编译后的文本，所以能直接看出「哪个节点多了/少了哪条属性」，
比在二进制上逐字节比要可读得多。

例如拿原厂树和我们在用的 51 KB dtb 比：

```sh
python tools/dtb/dtb2dts.py --diff \
  docs/bringup/ufi003-mb-v02/vendor-dtb-board8-subtype0x100.dtb \
  drivertree/msm8916-zhihe-ufi003-mb-v02.dtb | wc -l
# 9169 行差异 —— 原厂是通用 MTP 树，我们在用的是上游风格设备树，两者结构差别很大
```

---

## 7. 反编译是不是无损的：往返验证

本机没有 `dtc`、`cpp`、`gcc`，所以「反编译出来的 dts 到底忠不忠于原文件」不能靠肉眼判断。
`tools/dtb/dts2dtb.py` 把这个判断变成可执行的一步：把 dts 编译回 dtb，和原文件逐字节比。

```sh
python tools/dtb/dts2dtb.py vendor-dts.dts \
  -o /tmp/rt.dtb --verify vendor-dtb-board8-subtype0x100.dtb
# IDENTICAL to vendor-dtb-board8-subtype0x100.dtb (144,551 B)
```

结果：

| dtb | 大小 | 节点 / 属性 | 往返结果 |
|---|---|---|---|
| `vendor-dtb-board8-subtype0x100.dtb` | 144,551 B | 873 / 4,947 | **IDENTICAL** |
| `drivertree/msm8916-zhihe-ufi003-mb-v02.dtb` | 51,342 B | 448 / 1,758 | **IDENTICAL** |
| 原厂 boot.img 里的 dtb-00 | 162,799 B | — | **IDENTICAL** |
| dtb-08 | 152,204 B | — | **IDENTICAL** |
| dtb-20 | 164,789 B | — | **IDENTICAL** |

字节完全一致，不是「结构等价」。也就是说这份 `.dts` 忠实描述了原 dtb 的每一个节点和属性值。

### 实现上唯一需要对齐的地方

第一次跑差 26 字节，`strings` 块偏大。原因是 dtc 不只对属性名做**完全相同**的去重，
还会把一个名字当作另一个的后缀来复用 —— `reg` 指向 `qcom,reg` 中间那个位置。
加上这个后缀复用后，才做到字节一致。

### 「无损」的边界

可逆的：节点树、节点顺序、属性顺序、属性名、属性值、phandle 数值。

不可逆的（这些信息根本不在二进制里，不是工具能力问题）：

- `#include` 结构 —— dtb 是预处理后的产物
- 标签名（`&tlmm`、`&mpss`）—— 除非 dtb 带 `__symbols__` 节点，这个不带
- 注释、条件编译、`#define` 常量
- 属性值的**写法**（`<0x1>` 还是 `<&phandle 0>`，编译后都是同一个 4 字节）

所以正确的用法是：把这份 dts 当**硬件事实的权威参考**，不是当可维护源码。
要改我们的树，改 `tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts`（继承上游 dtsi 的那份）。

