# 设备树对照：vendor vs 在用

- vendor: `vendor-dtb-board8-subtype0x100.dtb` — 873 节点，221 个带地址
- ours  : `msm8916-zhihe-ufi003-mb-v02.dtb` — 448 节点，126 个带地址
- 地址匹配 **80** 个硬件控制器；仅 vendor 138，仅 ours 43

另有 **3** 个控制器两边都有，但节点名里的地址写法不同（一边写寄存器块基址、一边写块内偏移），已按同一硬件合并对比：

| vendor 节点 | ours 节点 |
|---|---|
| `qcom,rpm-master-stats@60150` | `sram@60000` |
| `sdhci@07824000` | `mmc@7824900` |
| `sdhci@07864000` | `mmc@7864900` |

## 重点发现

### vendor 启用、我们关掉了

按 DT 规范 `status` 缺失等于 `okay`，所以 vendor 树里没写 `status` 的节点在 Android 下是工作的。下面这些我们显式关掉了，逐个确认是有意为之还是漏了。

| 地址 | 节点 | 子系统 | vendor | ours |
|---|---|---|---|---|
| `@1000` | `charger@1000` | 电源/PMIC（非关键子系统） | okay | disabled |
| `@4000` | `battery@4000` | 电源/PMIC（非关键子系统） | okay | disabled |
| `@f000` | `audio-codec@f000` | 音频（非关键子系统） | okay | disabled |
| `@802000` | `stm@802000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@810000` | `cti@810000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@811000` | `cti@811000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@820000` | `tpiu@820000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@821000` | `funnel@821000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@824000` | `replicator@824000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@825000` | `etf@825000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@826000` | `etr@826000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@841000` | `funnel@841000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@858000` | `cti@858000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@859000` | `cti@859000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85a000` | `cti@85a000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85b000` | `cti@85b000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85c000` | `etm@85c000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85d000` | `etm@85d000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85e000` | `etm@85e000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@85f000` | `etm@85f000` | 调试/追踪（非关键子系统） | okay | disabled |
| `@1a00000` | `display-subsystem@1a00000` | 显示（非关键子系统） | okay | disabled |
| `@1b0ac00` | `camss@1b0ac00` | 摄像头（非关键子系统） | okay | disabled |
| `@1b0c000` | `cci@1b0c000` | 摄像头（非关键子系统） | okay | disabled |
| `@1c00000` | `gpu@1c00000` | GPU/视频（非关键子系统） | okay | disabled |
| `@78af000` | `serial@78af000` | 串口（非关键子系统） | ok | disabled |
| `@78b9000` | `i2c@78b9000` | I2C/SPI（非关键子系统） | okay | disabled |

### 其它关键属性差异

`dr_mode` / `bus-width` / `*-supply` 这类属性决定设备怎么接、能不能供上电，不一致就值得逐条确认。

| 地址 | vendor 节点 | ours 节点 | 差异 |
|---|---|---|---|
| `@78d9000` | `usb@78d9000` | `usb@78d9000` | `dr_mode` (absent) → "peripheral"; `phy-names` (absent) → "usb-phy" |
| `@7824000` | `sdhci@07824000` | `mmc@7824900` | `bus-width` (absent) → <0x8>; `non-removable` (absent) → (empty) |
| `@7864000` | `sdhci@07864000` | `mmc@7864900` | `bus-width` (absent) → <0x4>; `vmmc-supply` (absent) → <0x6c>; `vqmmc-supply` (absent) → <0x6d> |

### 关键子系统里 vendor 有、我们没有

**USB**

- `/soc/qcom,usbbam@78c4000`  
  `qcom,usb-bam-msm`
- `/soc/android_usb@086000c8`  
  `qcom,android-usb`

**网络**

- `/soc/qcom,wcnss-wlan@0a000000`  
  `qcom,wcnss_wlan`
- `/soc/qcom,pronto@a21b000`  
  `qcom,pil-tz-generic`

## 各子系统节点数

| 子系统 | vendor | ours | 差额 |
|---|---:|---:|---:|
| USB | 12 | 6 | +6 |
| SIM/Modem | 124 | 72 | +52 |
| 网络 | 8 | 5 | +3 |
| 存储 | 6 | 2 | +4 |
| 显示 | 32 | 9 | +23 |
| 音频 | 63 | 15 | +48 |
| 电源/PMIC | 118 | 62 | +56 |
| 时钟/复位 | 34 | 13 | +21 |
| IOMMU/中断 | 36 | 8 | +28 |
| GPIO/按键/LED | 200 | 74 | +126 |
| 串口 | 4 | 2 | +2 |
| I2C/SPI | 11 | 13 | -2 |
| GPU/视频 | 13 | 10 | +3 |
| 摄像头 | 9 | 8 | +1 |
| 调试/追踪 | 43 | 67 | -24 |
| CPU/拓扑 | 26 | 26 | +0 |
| 内存/保留区 | 11 | 10 | +1 |
| 其它 | 123 | 46 | +77 |

## 同一硬件，属性差异

按 `@地址` 配对。已排除 phandle、`#*-cells`、`clocks` 这类结构性噪音。

### `@0` — vendor `cpu@0` / ours `cpu@0`

- vendor 路径 `/cpus/cpu@0`
- ours   路径 `/cpus/cpu@0`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,armv8" | "arm,cortex-a53" |
| `enable-method` | "qcom,arm-cortex-acc" | "psci" |
| `operating-points-v2` | (absent) | <0x6> |
| `power-domain-names` | (absent) | "psci" |
| `power-domains` | (absent) | <0x7> |
| `qcom,saw` | (absent) | <0x9> |

### `@1` — vendor `cpu@1` / ours `cpu@1`

- vendor 路径 `/cpus/cpu@1`
- ours   路径 `/cpus/cpu@1`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,armv8" | "arm,cortex-a53" |
| `enable-method` | "qcom,arm-cortex-acc" | "psci" |
| `operating-points-v2` | (absent) | <0x6> |
| `power-domain-names` | (absent) | "psci" |
| `power-domains` | (absent) | <0xa> |
| `qcom,saw` | (absent) | <0xc> |

### `@2` — vendor `cpu@2` / ours `cpu@2`

- vendor 路径 `/cpus/cpu@2`
- ours   路径 `/cpus/cpu@2`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,armv8" | "arm,cortex-a53" |
| `enable-method` | "qcom,arm-cortex-acc" | "psci" |
| `operating-points-v2` | (absent) | <0x6> |
| `power-domain-names` | (absent) | "psci" |
| `power-domains` | (absent) | <0xd> |
| `qcom,saw` | (absent) | <0xf> |

### `@3` — vendor `cpu@3` / ours `cpu@3`

- vendor 路径 `/cpus/cpu@3`
- ours   路径 `/cpus/cpu@3`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,armv8" | "arm,cortex-a53" |
| `enable-method` | "qcom,arm-cortex-acc" | "psci" |
| `operating-points-v2` | (absent) | <0x6> |
| `power-domain-names` | (absent) | "psci" |
| `power-domains` | (absent) | <0x10> |
| `qcom,saw` | (absent) | <0x12> |

### `@7` — vendor `chan@7` / ours `channel@7`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@7`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/adc@3100/channel@7`

| 属性 | vendor | ours |
|---|---|---|
| `label` | "vph_pwr" | (absent) |
| `qcom,calibration-type` | "absolute" | (absent) |
| `qcom,decimation` | <0x0> | (absent) |
| `qcom,fast-avg-setup` | <0x0> | (absent) |
| `qcom,hw-settle-time` | <0x0> | (absent) |
| `qcom,pre-div-channel-scaling` | <0x1> | (absent) |
| `qcom,pre-scaling` | (absent) | <0x1 0x3> |
| `qcom,scale-function` | <0x0> | (absent) |

### `@8` — vendor `chan@8` / ours `channel@8`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@8`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/adc@3100/channel@8`

| 属性 | vendor | ours |
|---|---|---|
| `label` | "die_temp" | (absent) |
| `qcom,calibration-type` | "absolute" | (absent) |
| `qcom,decimation` | <0x0> | (absent) |
| `qcom,fast-avg-setup` | <0x0> | (absent) |
| `qcom,hw-settle-time` | <0x0> | (absent) |
| `qcom,pre-div-channel-scaling` | <0x0> | (absent) |
| `qcom,scale-function` | <0x3> | (absent) |

### `@9` — vendor `chan@9` / ours `channel@9`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@9`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/adc@3100/channel@9`

| 属性 | vendor | ours |
|---|---|---|
| `label` | "ref_625mv" | (absent) |
| `qcom,calibration-type` | "absolute" | (absent) |
| `qcom,decimation` | <0x0> | (absent) |
| `qcom,fast-avg-setup` | <0x0> | (absent) |
| `qcom,hw-settle-time` | <0x0> | (absent) |
| `qcom,pre-div-channel-scaling` | <0x0> | (absent) |
| `qcom,scale-function` | <0x0> | (absent) |

### `@a` — vendor `chan@a` / ours `channel@a`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@a`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/adc@3100/channel@a`

| 属性 | vendor | ours |
|---|---|---|
| `label` | "ref_1250v" | (absent) |
| `qcom,calibration-type` | "absolute" | (absent) |
| `qcom,decimation` | <0x0> | (absent) |
| `qcom,fast-avg-setup` | <0x0> | (absent) |
| `qcom,hw-settle-time` | <0x0> | (absent) |
| `qcom,pre-div-channel-scaling` | <0x0> | (absent) |
| `qcom,scale-function` | <0x0> | (absent) |

### `@800` — vendor `qcom,power-on@800` / ours `pon@800`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,power-on@800`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/pon@800`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,qpnp-power-on" | "qcom,pm8916-pon" |
| `interrupt-names` | "kpdpwr", "resin" | (absent) |
| `interrupts` | <0x0 0x8 0x0 0x0 0x8 0x1> | (absent) |
| `mode-bootloader` | (absent) | <0x2> |
| `mode-recovery` | (absent) | <0x1> |
| `qcom,clear-warm-reset` | (empty) | (absent) |
| `qcom,pon-dbc-delay` | <0x3d09> | (absent) |
| `qcom,system-reset` | (empty) | (absent) |
| `reg` | <0x800 0x100> | <0x800> |

### `@1000` — vendor `qcom,chgr@1000` / ours `charger@1000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,charger/qcom,chgr@1000`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/charger@1000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8916-lbc" |
| `interrupt-names` | "chg-done", "chg-failed", "fast-chg-on", "vbat-det-lo" | "vbat_det", "fast_chg", "chg_fail", "chg_done", "bat_pres", "temp_ok", "coarse_det", "usb_vbus", "chg_gone", " |
| `interrupts` | <0x0 0x10 0x7 0x0 0x10 0x6 0x0 0x10 0x5 0x0 0x10 0x0> | <0x0 0x10 0x0 0x3 0x0 0x10 0x5 0x3 0x0 0x10 0x6 0x3 0x0 0x10 0x7 0x3 0x0 0x12 0x0 0x3 0x0 0x12 0x1 0x3 0x0 0x1 |
| `reg` | <0x1000 0x100> | <0x1000 0x1200 0x1300 0x1600> |
| `reg-names` | (absent) | "chgr", "bat_if", "usb", "misc" |
| `status` | (absent) | "disabled" |

### `@1300` — vendor `qcom,usb-chgpth@1300` / ours `usb-detect@1300`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,charger/qcom,usb-chgpth@1300`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/usb-detect@1300`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8941-misc" |
| `interrupt-names` | "usb-over-temp", "chg-gone", "usbin-valid" | "usb_vbus" |
| `interrupts` | <0x0 0x13 0x4 0x0 0x13 0x2 0x0 0x13 0x1> | <0x0 0x13 0x1 0x3> |
| `reg` | <0x1300 0x100> | <0x1300> |
| `status` | (absent) | "okay" |

### `@2400` — vendor `qcom,temp-alarm@2400` / ours `temp-alarm@2400`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,temp-alarm@2400`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/temp-alarm@2400`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,qpnp-temp-alarm" | "qcom,spmi-temp-alarm" |
| `interrupts` | <0x0 0x24 0x0> | <0x0 0x24 0x0 0x1> |
| `io-channel-names` | (absent) | "thermal" |
| `io-channels` | (absent) | <0x56 0x8> |
| `label` | "pm8916_tz" | (absent) |
| `qcom,channel-num` | <0x8> | (absent) |
| `qcom,temp_alarm-vadc` | <0xce> | (absent) |
| `qcom,threshold-set` | <0x0> | (absent) |
| `reg` | <0x2400 0x100> | <0x2400> |

### `@3100` — vendor `vadc@3100` / ours `adc@3100`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/adc@3100`

| 属性 | vendor | ours |
|---|---|---|
| `#io-channel-cells` | (absent) | <0x1> |
| `compatible` | "qcom,qpnp-vadc" | "qcom,spmi-vadc" |
| `interrupt-names` | "eoc-int-en-set" | (absent) |
| `interrupts` | <0x0 0x31 0x0> | <0x0 0x31 0x0 0x1> |
| `qcom,adc-bit-resolution` | <0xf> | (absent) |
| `qcom,adc-vdd-reference` | <0x708> | (absent) |
| `qcom,pmic-revid` | <0xcd> | (absent) |
| `qcom,vadc-poll-eoc` | (empty) | (absent) |
| `reg` | <0x3100 0x100> | <0x3100> |

### `@4000` — vendor `qcom,vm-bms@4000` / ours `battery@4000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,vmbms/qcom,vm-bms@4000`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/battery@4000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8916-bms-vm" |
| `interrupt-names` | "leave_cv", "enter_cv", "good_ocv", "ocv_thr", "fifo_update_done", "fsm_state_change" | "cv_leave", "cv_enter", "ocv_good", "ocv_thr", "fifo", "state_chg" |
| `interrupts` | <0x0 0x40 0x0 0x0 0x40 0x1 0x0 0x40 0x2 0x0 0x40 0x3 0x0 0x40 0x4 0x0 0x40 0x5> | <0x0 0x40 0x0 0x1 0x0 0x40 0x1 0x1 0x0 0x40 0x2 0x1 0x0 0x40 0x3 0x1 0x0 0x40 0x4 0x1 0x0 0x40 0x5 0x1> |
| `reg` | <0x4000 0x100> | <0x4000> |
| `status` | (absent) | "disabled" |

### `@6000` — vendor `qcom,pm8916_rtc_rw@6000` / ours `rtc@6000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,pm8916_rtc/qcom,pm8916_rtc_rw@6000`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/rtc@6000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8941-rtc" |
| `interrupts` | (absent) | <0x0 0x61 0x1 0x1> |
| `reg` | <0x6000 0x100> | <0x6000 0x6100> |
| `reg-names` | (absent) | "rtc", "alarm" |

### `@a000` — vendor `mpp@a000` / ours `mpps@a000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/mpps/mpp@a000`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/mpps@a000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8916-mpp", "qcom,spmi-mpp" |
| `gpio-controller` | (absent) | (empty) |
| `gpio-ranges` | (absent) | <0x57 0x0 0x0 0x4> |
| `interrupt-controller` | (absent) | (empty) |
| `qcom,pin-num` | <0x1> | (absent) |
| `reg` | <0xa000 0x100> | <0xa000> |
| `status` | "disabled" | (absent) |

### `@c000` — vendor `gpio@c000` / ours `gpio@c000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@0/gpios/gpio@c000`
- ours   路径 `/soc@0/spmi@200f000/pmic@0/gpio@c000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | (absent) | "qcom,pm8916-gpio", "qcom,spmi-gpio" |
| `gpio-controller` | (absent) | (empty) |
| `gpio-ranges` | (absent) | <0x58 0x0 0x0 0x4> |
| `interrupt-controller` | (absent) | (empty) |
| `qcom,pin-num` | <0x1> | (absent) |
| `reg` | <0xc000 0x100> | <0xc000> |
| `status` | "disabled" | (absent) |

### `@f000` — vendor `msm8x16_wcd_codec@f000` / ours `audio-codec@f000`

- vendor 路径 `/soc/qcom,spmi@200f000/qcom,pm8916@1/msm8x16_wcd_codec@f000`
- ours   路径 `/soc@0/spmi@200f000/pmic@1/audio-codec@f000`

| 属性 | vendor | ours |
|---|---|---|
| `cdc-vdd-mic-bias-supply` | <0xa9> | (absent) |
| `cdc-vdd-pa-supply` | <0xab> | (absent) |
| `cdc-vdd-px-supply` | <0xd1> | (absent) |
| `cdc-vdda-cp-supply` | <0xd1> | (absent) |
| `cdc-vdda-h-supply` | <0xab> | (absent) |
| `compatible` | "qcom,wcd-spmi" | "qcom,pm8916-wcd-analog-codec" |
| `interrupt-names` | "spk_cnp_int", "spk_clip_int", "spk_ocp_int", "ins_rem_det1", "but_rel_det", "but_press_det", "ins_rem_det", " | "cdc_spk_cnp_int", "cdc_spk_clip_int", "cdc_spk_ocp_int", "mbhc_ins_rem_det1", "mbhc_but_rel_det", "mbhc_but_p |
| `interrupts` | <0x1 0xf0 0x0 0x1 0xf0 0x1 0x1 0xf0 0x2 0x1 0xf0 0x3 0x1 0xf0 0x4 0x1 0xf0 0x5 0x1 0xf0 0x6 0x1 0xf0 0x7> | <0x1 0xf0 0x0 0x0 0x1 0xf0 0x1 0x0 0x1 0xf0 0x2 0x0 0x1 0xf0 0x3 0x0 0x1 0xf0 0x4 0x0 0x1 0xf0 0x5 0x0 0x1 0xf |
| `qcom,cdc-mclk-clk-rate` | <0x927c00> | (absent) |
| `qcom,cdc-on-demand-supplies` | "cdc-vdd-mic-bias" | (absent) |
| `qcom,cdc-static-supplies` | "cdc-vdda-h", "cdc-vdd-px", "cdc-vdd-pa", "cdc-vdda-cp" | (absent) |
| `qcom,cdc-vdd-mic-bias-current` | <0x61a8> | (absent) |
| `qcom,cdc-vdd-mic-bias-voltage` | <0x2eebb8 0x2eebb8> | (absent) |
| `qcom,cdc-vdd-pa-current` | <0x1388> | (absent) |
| `qcom,cdc-vdd-pa-voltage` | <0x1b7740 0x1b7740> | (absent) |
| `qcom,cdc-vdd-px-current` | <0xbbfd0> | (absent) |
| `qcom,cdc-vdd-px-voltage` | <0x1b7740 0x2191c0> | (absent) |
| `qcom,cdc-vdda-cp-current` | <0xbbfd0> | (absent) |
| `qcom,cdc-vdda-cp-voltage` | <0x1b7740 0x2191c0> | (absent) |
| `qcom,cdc-vdda-h-current` | <0x4e20> | (absent) |
| … | 另有 6 条 | |

### `@22000` — vendor `qrng@22000` / ours `rng@22000`

- vendor 路径 `/soc/qrng@22000`
- ours   路径 `/soc@0/rng@22000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,msm-rng" | "qcom,prng" |
| `qcom,msm-bus,name` | "msm-rng-noc" | (absent) |
| `qcom,msm-bus,num-cases` | <0x2> | (absent) |
| `qcom,msm-bus,num-paths` | <0x1> | (absent) |
| `qcom,msm-bus,vectors-KBps` | <0x1 0x26a 0x0 0x0 0x1 0x26a 0x0 0x320> | (absent) |
| `qcom,msm-rng-iface-clk` | (empty) | (absent) |
| `status` | "okay" | (absent) |

### `@802000` — vendor `stm@802000` / ours `stm@802000`

- vendor 路径 `/soc/stm@802000`
- ours   路径 `/soc@0/stm@802000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-stm" | "arm,coresight-stm", "arm,primecell" |
| `coresight-child-list` | <0x31> | (absent) |
| `coresight-child-ports` | <0x7> | (absent) |
| `coresight-id` | <0x8> | (absent) |
| `coresight-name` | "coresight-stm" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `reg-names` | "stm-base", "stm-data-base" | "stm-base", "stm-stimulus-base" |
| `status` | (absent) | "disabled" |

### `@810000` — vendor `cti@810000` / ours `cti@810000`

- vendor 路径 `/soc/cti@810000`
- ours   路径 `/soc@0/cti@810000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti", "arm,primecell" |
| `coresight-id` | <0x11> | (absent) |
| `coresight-name` | "coresight-cti0" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@811000` — vendor `cti@811000` / ours `cti@811000`

- vendor 路径 `/soc/cti@811000`
- ours   路径 `/soc@0/cti@811000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti", "arm,primecell" |
| `coresight-id` | <0x12> | (absent) |
| `coresight-name` | "coresight-cti1" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@820000` — vendor `tpiu@820000` / ours `tpiu@820000`

- vendor 路径 `/soc/tpiu@820000`
- ours   路径 `/soc@0/tpiu@820000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-tpiu" | "arm,coresight-tpiu", "arm,primecell" |
| `coresight-id` | <0x1> | (absent) |
| `coresight-name` | "coresight-tpiu" | (absent) |
| `coresight-nr-inports` | <0x1> | (absent) |
| `interrupt-names` | "nidnt-irq" | (absent) |
| `interrupts` | <0x0 0x52 0x0> | (absent) |
| `nidnt-gpio` | <0x26> | (absent) |
| `nidnt-gpio-polarity` | <0x1> | (absent) |
| `pinctrl-0` | <0xd 0xe 0xf 0x10 0x11 0x12> | (absent) |
| `pinctrl-1` | <0x13 0x14 0x15 0x16 0x17 0x18> | (absent) |
| `pinctrl-2` | <0x19 0x1a 0x1b 0x1c 0x1d> | (absent) |
| `pinctrl-3` | <0x1e 0x1f 0x20 0x21 0x22 0x23> | (absent) |
| `pinctrl-4` | <0x24 0x25 0x26 0x27 0x28> | (absent) |
| `pinctrl-5` | <0x29 0x2a 0x2b 0x2c> | (absent) |
| `pinctrl-names` | "sdcard", "trace", "swduart", "swdtrc", "jtag", "spmi" | (absent) |
| `qcom,nidnt-jtag` | (empty) | (absent) |
| `qcom,nidnt-spmi` | (empty) | (absent) |
| `qcom,nidnt-swdtrc` | (empty) | (absent) |
| `qcom,nidnt-swduart` | (empty) | (absent) |
| `qcom,nidnthw` | (empty) | (absent) |
| … | 另有 9 条 | |

### `@821000` — vendor `funnel@821000` / ours `funnel@821000`

- vendor 路径 `/soc/funnel@821000`
- ours   路径 `/soc@0/funnel@821000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-funnel" | "arm,coresight-dynamic-funnel", "arm,primecell" |
| `coresight-child-list` | <0x30> | (absent) |
| `coresight-child-ports` | <0x0> | (absent) |
| `coresight-id` | <0x4> | (absent) |
| `coresight-name` | "coresight-funnel-in0" | (absent) |
| `coresight-nr-inports` | <0x8> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `reg-names` | "funnel-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@824000` — vendor `replicator@824000` / ours `replicator@824000`

- vendor 路径 `/soc/replicator@824000`
- ours   路径 `/soc@0/replicator@824000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,coresight-replicator" | "arm,coresight-dynamic-replicator", "arm,primecell" |
| `coresight-child-list` | <0x2d 0x2e> | (absent) |
| `coresight-child-ports` | <0x0 0x0> | (absent) |
| `coresight-id` | <0x2> | (absent) |
| `coresight-name` | "coresight-replicator" | (absent) |
| `coresight-nr-inports` | <0x1> | (absent) |
| `coresight-outports` | <0x0 0x1> | (absent) |
| `reg-names` | "replicator-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@825000` — vendor `tmc@825000` / ours `etf@825000`

- vendor 路径 `/soc/tmc@825000`
- ours   路径 `/soc@0/etf@825000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-tmc" | "arm,coresight-tmc", "arm,primecell" |
| `coresight-child-list` | <0x2f> | (absent) |
| `coresight-child-ports` | <0x0> | (absent) |
| `coresight-ctis` | <0x8 0x9> | (absent) |
| `coresight-default-sink` | (empty) | (absent) |
| `coresight-id` | <0x3> | (absent) |
| `coresight-name` | "coresight-tmc-etf" | (absent) |
| `coresight-nr-inports` | <0x1> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `qcom,tmc-flush-powerdown` | (empty) | (absent) |
| `reg-names` | "tmc-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@826000` — vendor `tmc@826000` / ours `etr@826000`

- vendor 路径 `/soc/tmc@826000`
- ours   路径 `/soc@0/etr@826000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-tmc" | "arm,coresight-tmc", "arm,primecell" |
| `coresight-ctis` | <0x8 0x9> | (absent) |
| `coresight-id` | <0x0> | (absent) |
| `coresight-name` | "coresight-tmc-etr" | (absent) |
| `coresight-nr-inports` | <0x1> | (absent) |
| `interrupt-names` | "byte-cntr-irq" | (absent) |
| `interrupts` | <0x0 0xa6 0x0> | (absent) |
| `qcom,memory-size` | <0x100000> | (absent) |
| `qcom,tmc-flush-powerdown` | (empty) | (absent) |
| `reg` | <0x826000 0x1000 0x884000 0x15000> | <0x826000 0x1000> |
| `reg-names` | "tmc-base", "bam-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@841000` — vendor `funnel@841000` / ours `funnel@841000`

- vendor 路径 `/soc/funnel@841000`
- ours   路径 `/soc@0/funnel@841000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "arm,coresight-funnel" | "arm,coresight-dynamic-funnel", "arm,primecell" |
| `coresight-child-list` | <0x31> | (absent) |
| `coresight-child-ports` | <0x4> | (absent) |
| `coresight-id` | <0x5> | (absent) |
| `coresight-name` | "coresight-funnel-apss" | (absent) |
| `coresight-nr-inports` | <0x4> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `qcom,funnel-save-restore` | (empty) | (absent) |
| `reg-names` | "funnel-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@858000` — vendor `cti@858000` / ours `cti@858000`

- vendor 路径 `/soc/cti@858000`
- ours   路径 `/soc@0/cti@858000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,cs-dev-assoc` | (absent) | <0x41> |
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti-v8-arch", "arm,coresight-cti", "arm,primecell" |
| `coresight-cti-cpu` | <0x34> | (absent) |
| `coresight-id` | <0x1a> | (absent) |
| `coresight-name` | "coresight-cti-cpu0" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3d> |
| `qcom,cti-save` | (empty) | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@859000` — vendor `cti@859000` / ours `cti@859000`

- vendor 路径 `/soc/cti@859000`
- ours   路径 `/soc@0/cti@859000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,cs-dev-assoc` | (absent) | <0x42> |
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti-v8-arch", "arm,coresight-cti", "arm,primecell" |
| `coresight-cti-cpu` | <0x35> | (absent) |
| `coresight-id` | <0x1b> | (absent) |
| `coresight-name` | "coresight-cti-cpu1" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3e> |
| `qcom,cti-save` | (empty) | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85a000` — vendor `cti@85a000` / ours `cti@85a000`

- vendor 路径 `/soc/cti@85a000`
- ours   路径 `/soc@0/cti@85a000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,cs-dev-assoc` | (absent) | <0x43> |
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti-v8-arch", "arm,coresight-cti", "arm,primecell" |
| `coresight-cti-cpu` | <0x36> | (absent) |
| `coresight-id` | <0x1c> | (absent) |
| `coresight-name` | "coresight-cti-cpu2" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3f> |
| `qcom,cti-save` | (empty) | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85b000` — vendor `cti@85b000` / ours `cti@85b000`

- vendor 路径 `/soc/cti@85b000`
- ours   路径 `/soc@0/cti@85b000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,cs-dev-assoc` | (absent) | <0x44> |
| `compatible` | "arm,coresight-cti" | "arm,coresight-cti-v8-arch", "arm,coresight-cti", "arm,primecell" |
| `coresight-cti-cpu` | <0x37> | (absent) |
| `coresight-id` | <0x1d> | (absent) |
| `coresight-name` | "coresight-cti-cpu3" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x40> |
| `qcom,cti-save` | (empty) | (absent) |
| `reg-names` | "cti-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85c000` — vendor `etm@85c000` / ours `etm@85c000`

- vendor 路径 `/soc/etm@85c000`
- ours   路径 `/soc@0/etm@85c000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,coresight-loses-context-with-cpu` | (absent) | (empty) |
| `compatible` | "arm,coresight-etmv4" | "arm,coresight-etm4x", "arm,primecell" |
| `coresight-child-list` | <0x33> | (absent) |
| `coresight-child-ports` | <0x0> | (absent) |
| `coresight-etm-cpu` | <0x34> | (absent) |
| `coresight-id` | <0xa> | (absent) |
| `coresight-name` | "coresight-etm0" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3d> |
| `qcom,round-robin` | (empty) | (absent) |
| `reg-names` | "etm-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85d000` — vendor `etm@85d000` / ours `etm@85d000`

- vendor 路径 `/soc/etm@85d000`
- ours   路径 `/soc@0/etm@85d000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,coresight-loses-context-with-cpu` | (absent) | (empty) |
| `compatible` | "arm,coresight-etmv4" | "arm,coresight-etm4x", "arm,primecell" |
| `coresight-child-list` | <0x33> | (absent) |
| `coresight-child-ports` | <0x1> | (absent) |
| `coresight-etm-cpu` | <0x35> | (absent) |
| `coresight-id` | <0xb> | (absent) |
| `coresight-name` | "coresight-etm1" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3e> |
| `qcom,round-robin` | (empty) | (absent) |
| `reg-names` | "etm-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85e000` — vendor `etm@85e000` / ours `etm@85e000`

- vendor 路径 `/soc/etm@85e000`
- ours   路径 `/soc@0/etm@85e000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,coresight-loses-context-with-cpu` | (absent) | (empty) |
| `compatible` | "arm,coresight-etmv4" | "arm,coresight-etm4x", "arm,primecell" |
| `coresight-child-list` | <0x33> | (absent) |
| `coresight-child-ports` | <0x2> | (absent) |
| `coresight-etm-cpu` | <0x36> | (absent) |
| `coresight-id` | <0xc> | (absent) |
| `coresight-name` | "coresight-etm2" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x3f> |
| `qcom,round-robin` | (empty) | (absent) |
| `reg-names` | "etm-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@85f000` — vendor `etm@85f000` / ours `etm@85f000`

- vendor 路径 `/soc/etm@85f000`
- ours   路径 `/soc@0/etm@85f000`

| 属性 | vendor | ours |
|---|---|---|
| `arm,coresight-loses-context-with-cpu` | (absent) | (empty) |
| `compatible` | "arm,coresight-etmv4" | "arm,coresight-etm4x", "arm,primecell" |
| `coresight-child-list` | <0x33> | (absent) |
| `coresight-child-ports` | <0x3> | (absent) |
| `coresight-etm-cpu` | <0x37> | (absent) |
| `coresight-id` | <0xd> | (absent) |
| `coresight-name` | "coresight-etm3" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `cpu` | (absent) | <0x40> |
| `qcom,round-robin` | (empty) | (absent) |
| `reg-names` | "etm-base" | (absent) |
| `status` | (absent) | "disabled" |

### `@1000000` — vendor `pinctrl@1000000` / ours `pinctrl@1000000`

- vendor 路径 `/soc/pinctrl@1000000`
- ours   路径 `/soc@0/pinctrl@1000000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,msm-tlmm-v4" | "qcom,msm8916-pinctrl" |
| `gpio-controller` | (absent) | (empty) |
| `gpio-ranges` | (absent) | <0x49 0x0 0x0 0x7a> |
| `interrupt-controller` | (absent) | (empty) |
| `interrupts` | <0x0 0xd0 0x0> | <0x0 0xd0 0x4> |

### `@1800000` — vendor `qcom,gcc@1800000` / ours `clock-controller@1800000`

- vendor 路径 `/soc/qcom,gcc@1800000`
- ours   路径 `/soc@0/clock-controller@1800000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,gcc-8916" | "qcom,gcc-msm8916" |
| `reg` | <0x1800000 0x80000 0xb016000 0x40> | <0x1800000 0x80000> |
| `reg-names` | "cc_base", "apcs_base" | (absent) |
| `vdd_dig-supply` | <0x43> | (absent) |
| `vdd_sr2_dig-supply` | <0x9f> | (absent) |
| `vdd_sr2_pll-supply` | <0xa0> | (absent) |

### `@1a00000` — vendor `qcom,mdss_mdp@1a00000` / ours `display-subsystem@1a00000`

- vendor 路径 `/soc/qcom,mdss_mdp@1a00000`
- ours   路径 `/soc@0/display-subsystem@1a00000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,mdss_mdp" | "qcom,mdss" |
| `interrupt-controller` | (absent) | (empty) |
| `interrupts` | <0x0 0x48 0x0> | <0x0 0x48 0x4> |
| `power-domains` | (absent) | <0x13 0x2> |
| `qcom,max-bandwidth-high-kbps` | <0x10c8e0> | (absent) |
| `qcom,max-bandwidth-low-kbps` | <0x10c8e0> | (absent) |
| `qcom,max-clk-rate` | <0x1312d000> | (absent) |
| `qcom,max-mixer-width` | <0x800> | (absent) |
| `qcom,mdp-settings` | <0x11e4 0x0 0x65048 0x8 0x65848 0x8 0x66048 0x8> | (absent) |
| `qcom,mdss-ab-factor` | <0x1 0x1> | (absent) |
| `qcom,mdss-clk-factor` | <0x69 0x64> | (absent) |
| `qcom,mdss-ctl-off` | <0x2000 0x2200 0x2400> | (absent) |
| `qcom,mdss-dspp-off` | <0x55000> | (absent) |
| `qcom,mdss-has-decimation` | (empty) | (absent) |
| `qcom,mdss-has-non-scalar-rgb` | (empty) | (absent) |
| `qcom,mdss-ib-factor` | <0x2 0x1> | (absent) |
| `qcom,mdss-intf-off` | <0x0 0x6b800> | (absent) |
| `qcom,mdss-mdp-reg-offset` | <0x1000> | (absent) |
| `qcom,mdss-mixer-intf-off` | <0x45000> | (absent) |
| `qcom,mdss-mixer-wb-off` | <0x48000> | (absent) |
| … | 另有 40 条 | |

### `@1a98000` — vendor `qcom,mdss_dsi@1a98000` / ours `dsi@1a98000`

- vendor 路径 `/soc/qcom,mdss_dsi@1a98000`
- ours   路径 `/soc@0/display-subsystem@1a00000/dsi@1a98000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,mdss-dsi-ctrl" | "qcom,msm8916-dsi-ctrl", "qcom,mdss-dsi-ctrl" |
| `gdsc-supply` | <0x42> | (absent) |
| `interrupts` | (absent) | <0x4> |
| `label` | "MDSS DSI CTRL->0" | (absent) |
| `phys` | (absent) | <0x4e> |
| `qcom,mdss-fb-map` | <0x46> | (absent) |
| `qcom,mdss-mdp` | <0x47> | (absent) |
| `qcom,mmss-phyreset-ctrl-offset` | <0x24> | (absent) |
| `qcom,mmss-ulp-clamp-ctrl-offset` | <0x20> | (absent) |
| `qcom,platform-bist-ctrl` | [00 00 b1 ff 00 00] | (absent) |
| `qcom,platform-lane-config` | [00 00 00 00 00 00 00 01 97 00 00 00 00 05 00 00 01 97 00 00 00 00 0a 00 00 01 97 00 00 00 00 0f 00 00 01 97 0 | (absent) |
| `qcom,platform-regulator-settings` | [03 08 07 00 20 07 01] | (absent) |
| `qcom,platform-strength-ctrl` | [ff 06] | (absent) |
| `reg` | <0x1a98000 0x25c 0x1a98500 0x2b0 0x193e000 0x30> | <0x1a98000 0x25c> |
| `reg-names` | "dsi_ctrl", "dsi_phy", "mmss_misc_phys" | "dsi_ctrl" |
| `vdd-supply` | <0x49> | (absent) |

### `@1a98300` — vendor `qcom,mdss_dsi_pll@1a98300` / ours `phy@1a98300`

- vendor 路径 `/soc/qcom,mdss_dsi_pll@1a98300`
- ours   路径 `/soc@0/display-subsystem@1a00000/phy@1a98300`

| 属性 | vendor | ours |
|---|---|---|
| `clock-rate` | <0x0> | (absent) |
| `compatible` | "qcom,mdss_dsi_pll_8916" | "qcom,dsi-phy-28nm-lp" |
| `gdsc-supply` | <0x42> | (absent) |
| `label` | "MDSS DSI 0 PLL" | (absent) |
| `reg` | <0x1a98300 0xd4> | <0x1a98300 0xd4 0x1a98500 0x280 0x1a98780 0x30> |
| `reg-names` | "pll_base" | "dsi_pll", "dsi_phy", "dsi_phy_regulator" |
| `status` | "disabled" | (absent) |

### `@1b0ac00` — vendor `qcom,csiphy@1b0ac00` / ours `camss@1b0ac00`

- vendor 路径 `/soc/qcom,csiphy@1b0ac00`
- ours   路径 `/soc@0/camss@1b0ac00`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,csiphy-v3.1", "qcom,csiphy" | "qcom,msm8916-camss" |
| `interrupt-names` | "csiphy" | "csiphy0", "csiphy1", "csid0", "csid1", "ispif", "vfe0" |
| `interrupts` | <0x0 0x4e 0x0> | <0x0 0x4e 0x1 0x0 0x4f 0x1 0x0 0x33 0x1 0x0 0x34 0x1 0x0 0x37 0x1 0x0 0x39 0x1> |
| `iommus` | (absent) | <0x4c 0x3> |
| `power-domains` | (absent) | <0x13 0x4> |
| `qcom,clock-rates` | <0x0 0x0 0xbebc200 0x0 0x0 0x0 0x0> | (absent) |
| `reg` | <0x1b0ac00 0x200 0x1b00030 0x4> | <0x1b0ac00 0x200 0x1b00030 0x4 0x1b0b000 0x200 0x1b00038 0x4 0x1b08000 0x100 0x1b08400 0x100 0x1b0a000 0x500 0 |
| `reg-names` | "csiphy", "csiphy_clk_mux" | "csiphy0", "csiphy0_clk_mux", "csiphy1", "csiphy1_clk_mux", "csid0", "csid1", "ispif", "csi_clk_mux", "vfe0" |
| `status` | (absent) | "disabled" |
| `vdda-supply` | (absent) | <0x4f> |

### `@1b0c000` — vendor `qcom,cci@1b0c000` / ours `cci@1b0c000`

- vendor 路径 `/soc/qcom,cci@1b0c000`
- ours   路径 `/soc@0/cci@1b0c000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,cci" | "qcom,msm8916-cci", "qcom,msm8226-cci" |
| `gpios` | <0x4f 0x1d 0x0 0x4f 0x1e 0x0> | (absent) |
| `interrupt-names` | "cci" | (absent) |
| `interrupts` | <0x0 0x32 0x0> | <0x0 0x32 0x1> |
| `pinctrl-0` | <0x9d> | <0x52> |
| `pinctrl-1` | <0x9e> | (absent) |
| `pinctrl-names` | "cci_default", "cci_suspend" | "default" |
| `qcom,clock-rates` | <0x0 0x124f800 0x4c4b400 0x0 0x0> | (absent) |
| `qcom,gpio-tbl-flags` | <0x1 0x1> | (absent) |
| `qcom,gpio-tbl-label` | "CCI_I2C_DATA0", "CCI_I2C_CLK0" | (absent) |
| `qcom,gpio-tbl-num` | <0x0 0x1> | (absent) |
| `reg-names` | "cci" | (absent) |
| `status` | (absent) | "disabled" |

### `@1c00000` — vendor `qcom,kgsl-3d0@01c00000` / ours `gpu@1c00000`

- vendor 路径 `/soc/qcom,kgsl-3d0@01c00000`
- ours   路径 `/soc@0/gpu@1c00000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,kgsl-3d0", "qcom,kgsl-3d" | "qcom,adreno-306.0", "qcom,adreno" |
| `coresight-child-list` | <0x31> | (absent) |
| `coresight-child-ports` | <0x5> | (absent) |
| `coresight-id` | <0x43> | (absent) |
| `coresight-name` | "coresight-gfx" | (absent) |
| `coresight-nr-inports` | <0x0> | (absent) |
| `coresight-outports` | <0x0> | (absent) |
| `interrupts` | <0x0 0x21 0x0> | <0x0 0x21 0x4> |
| `iommu` | <0x41> | (absent) |
| `iommus` | (absent) | <0x54 0x1 0x54 0x2> |
| `label` | "kgsl-3d0" | (absent) |
| `operating-points-v2` | (absent) | <0x53> |
| `power-domains` | (absent) | <0x13 0x5> |
| `qcom,chipid` | <0x3000600> | (absent) |
| `qcom,clk-map` | <0x5e> | (absent) |
| `qcom,id` | <0x0> | (absent) |
| `qcom,idle-timeout` | <0x8> | (absent) |
| `qcom,initial-pwrlevel` | <0x1> | (absent) |
| `qcom,msm-bus,name` | "grp3d" | (absent) |
| `qcom,msm-bus,num-cases` | <0x4> | (absent) |
| … | 另有 8 条 | |

### `@200f000` — vendor `qcom,spmi@200f000` / ours `spmi@200f000`

- vendor 路径 `/soc/qcom,spmi@200f000`
- ours   路径 `/soc@0/spmi@200f000`

| 属性 | vendor | ours |
|---|---|---|
| `interrupt-names` | (absent) | "periph_irq" |
| `interrupts` | <0x0 0xbe 0x0> | <0x0 0xbe 0x4> |
| `qcom,channel` | (absent) | <0x0> |
| `qcom,ee` | (absent) | <0x0> |
| `qcom,pmic-arb-channel` | <0x0> | (absent) |
| `qcom,pmic-arb-ee` | <0x0> | (absent) |

### `@4044000` — vendor `qcom,bam_dmux@4044000` / ours `dma-controller@4044000`

- vendor 路径 `/soc/qcom,bam_dmux@4044000`
- ours   路径 `/soc@0/dma-controller@4044000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,bam_dmux" | "qcom,bam-v1.7.0" |
| `interrupts` | <0x0 0x1d 0x1> | <0x0 0x1d 0x4> |
| `num-channels` | (absent) | <0x6> |
| `qcom,ee` | (absent) | <0x0> |
| `qcom,max-rx-mtu` | <0x1000> | (absent) |
| `qcom,num-ees` | (absent) | <0x1> |
| `qcom,powered-remotely` | (absent) | (empty) |
| `qcom,rx-ring-size` | <0x20> | (absent) |
| `status` | (absent) | "okay" |

### `@4080000` — vendor `qcom,mss@4080000` / ours `remoteproc@4080000`

- vendor 路径 `/soc/qcom,mss@4080000`
- ours   路径 `/soc@0/remoteproc@4080000`

| 属性 | vendor | ours |
|---|---|---|
| `active-clock-names` | "iface_clk", "bus_clk", "mem_clk" | (absent) |
| `compatible` | "qcom,pil-q6v56-mss" | "qcom,msm8916-mss-pil" |
| `cx-supply` | (absent) | <0x9f> |
| `interrupt-names` | (absent) | "wdog", "fatal", "ready", "handover", "stop-ack" |
| `interrupts` | <0x0 0x18 0x1> | (absent) |
| `interrupts-extended` | (absent) | <0x1 0x0 0x18 0x1 0x5c 0x0 0x1 0x5c 0x1 0x1 0x5c 0x2 0x1 0x5c 0x3 0x1> |
| `linux,contiguous-region` | <0xd8> | (absent) |
| `mx-supply` | (absent) | <0x9e> |
| `pinctrl-0` | (absent) | <0x61> |
| `pinctrl-names` | (absent) | "default" |
| `pll-supply` | (absent) | <0x9d> |
| `proxy-clock-names` | "xo" | (absent) |
| `qcom,firmware-name` | "modem" | (absent) |
| `qcom,gpio-err-fatal` | <0xd6 0x0 0x0> | (absent) |
| `qcom,gpio-err-ready` | <0xd6 0x1 0x0> | (absent) |
| `qcom,gpio-force-stop` | <0xd7 0x0 0x0> | (absent) |
| `qcom,gpio-proxy-unvote` | <0xd6 0x2 0x0> | (absent) |
| `qcom,gpio-ramdump-disable` | <0xd6 0xf 0x0> | (absent) |
| `qcom,gpio-stop-ack` | <0xd6 0x3 0x0> | (absent) |
| `qcom,halt-regs` | (absent) | <0x14 0x18000 0x19000 0x1a000> |
| … | 另有 14 条 | |

### `@78af000` — vendor `uart@78af000` / ours `serial@78af000`

- vendor 路径 `/soc/uart@78af000`
- ours   路径 `/soc@0/serial@78af000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,msm-hsuart-v14" | "qcom,msm-uartdm-v1.4", "qcom,msm-uartdm" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0x0 0x6e 0x1> |
| `interrupt-map` | <0x0 0x1 0x0 0x6b 0x0 0x1 0x1 0x0 0xee 0x0 0x2 0x4f 0x1 0x0> | (absent) |
| `interrupt-map-mask` | <0xffffffff> | (absent) |
| `interrupt-names` | "core_irq", "bam_irq", "wakeup_irq" | (absent) |
| `interrupts` | <0x0 0x1 0x2> | <0x0 0x6b 0x4> |
| `pinctrl-0` | <0xa5> | <0x6f> |
| `pinctrl-1` | <0xa6> | <0x70> |
| `pinctrl-names` | "sleep", "default" | "default", "sleep" |
| `qcom,bam-rx-ep-pipe-index` | <0x1> | (absent) |
| `qcom,bam-tx-ep-pipe-index` | <0x0> | (absent) |
| `qcom,inject-rx-on-wakeup` | <0x1> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,msm-bus,name` | "blsp1_uart1" | (absent) |
| `qcom,msm-bus,num-cases` | <0x2> | (absent) |
| `qcom,msm-bus,num-paths` | <0x1> | (absent) |
| `qcom,msm-bus,vectors-KBps` | <0x56 0x200 0x0 0x0 0x56 0x200 0x1f4 0x320> | (absent) |
| `qcom,rx-char-to-inject` | <0xfd> | (absent) |
| `reg` | <0x78af000 0x200 0x7884000 0x23000> | <0x78af000 0x200> |
| … | 另有 2 条 | |

### `@78b0000` — vendor `serial@78b0000` / ours `serial@78b0000`

- vendor 路径 `/soc/serial@78b0000`
- ours   路径 `/soc@0/serial@78b0000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,msm-lsuart-v14" | "qcom,msm-uartdm-v1.4", "qcom,msm-uartdm" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0x2 0x6e 0x3> |
| `interrupts` | <0x0 0x6c 0x0> | <0x0 0x6c 0x4> |
| `pinctrl-0` | <0xa7> | <0x71> |
| `pinctrl-1` | (absent) | <0x72> |
| `pinctrl-names` | "default" | "default", "sleep" |
| `status` | "ok" | "okay" |

### `@78b6000` — vendor `i2c@78b6000` / ours `i2c@78b6000`

- vendor 路径 `/soc/i2c@78b6000`
- ours   路径 `/soc@0/i2c@78b6000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,i2c-msm-v2" | "qcom,i2c-qup-v2.2.1" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0x6 0x6e 0x7> |
| `interrupt-names` | "qup_irq", "bam_irq" | (absent) |
| `interrupts` | <0x0 0x60 0x0 0x0 0xee 0x0> | <0x0 0x60 0x4> |
| `pinctrl-0` | <0xc5> | <0x77> |
| `pinctrl-1` | <0xc6> | <0x78> |
| `pinctrl-names` | "i2c_active", "i2c_sleep" | "default", "sleep" |
| `qcom,bam-pipe-idx-cons` | <0x6> | (absent) |
| `qcom,bam-pipe-idx-prod` | <0x7> | (absent) |
| `qcom,clk-freq-in` | <0x124f800> | (absent) |
| `qcom,clk-freq-out` | <0x186a0> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,noise-rjct-scl` | <0x0> | (absent) |
| `qcom,noise-rjct-sda` | <0x0> | (absent) |
| `reg` | <0x78b6000 0x600 0x7884000 0x23000> | <0x78b6000 0x500> |
| `reg-names` | "qup_phys_addr", "bam_phys_addr" | (absent) |

### `@78b7000` — vendor `spi@78b7000` / ours `spi@78b7000`

- vendor 路径 `/soc/spi@78b7000`
- ours   路径 `/soc@0/spi@78b7000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,spi-qup-v2" | "qcom,spi-qup-v2.2.1" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0x8 0x6e 0x9> |
| `interrupt-names` | "spi_irq", "spi_bam_irq" | (absent) |
| `interrupts` | <0x0 0x61 0x0 0x0 0xee 0x0> | <0x0 0x61 0x4> |
| `pinctrl-0` | <0xc1 0xc2> | <0x7d> |
| `pinctrl-1` | <0xc3 0xc4> | <0x7e> |
| `qcom,bam-consumer-pipe-index` | <0x8> | (absent) |
| `qcom,bam-producer-pipe-index` | <0x9> | (absent) |
| `qcom,infinite-mode` | <0x0> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,use-bam` | (empty) | (absent) |
| `qcom,use-pinctrl` | (empty) | (absent) |
| `qcom,ver-reg-exists` | (empty) | (absent) |
| `reg` | <0x78b7000 0x600 0x7884000 0x23000> | <0x78b7000 0x500> |
| `reg-names` | "spi_physical", "spi_bam_physical" | (absent) |
| `spi-max-frequency` | <0x2faf080> | (absent) |

### `@78b8000` — vendor `i2c@78b8000` / ours `i2c@78b8000`

- vendor 路径 `/soc/i2c@78b8000`
- ours   路径 `/soc@0/i2c@78b8000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,i2c-msm-v2" | "qcom,i2c-qup-v2.2.1" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0xa 0x6e 0xb> |
| `interrupt-names` | "qup_irq", "bam_irq" | (absent) |
| `interrupts` | <0x0 0x62 0x0 0x0 0xee 0x0> | <0x0 0x62 0x4> |
| `pinctrl-0` | <0xcb> | <0x7f> |
| `pinctrl-1` | <0xcc> | <0x80> |
| `pinctrl-names` | "i2c_active", "i2c_sleep" | "default", "sleep" |
| `qcom,bam-pipe-idx-cons` | <0xa> | (absent) |
| `qcom,bam-pipe-idx-prod` | <0xb> | (absent) |
| `qcom,clk-freq-in` | <0x124f800> | (absent) |
| `qcom,clk-freq-out` | <0x61a80> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,noise-rjct-scl` | <0x0> | (absent) |
| `qcom,noise-rjct-sda` | <0x0> | (absent) |
| `qcom,use-pinctrl` | (empty) | (absent) |
| `reg` | <0x78b8000 0x1000 0x7884000 0x23f00> | <0x78b8000 0x500> |
| `reg-names` | "qup_phys_addr", "bam_phys_addr" | (absent) |

### `@78b9000` — vendor `i2c@78b9000` / ours `i2c@78b9000`

- vendor 路径 `/soc/i2c@78b9000`
- ours   路径 `/soc@0/i2c@78b9000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,i2c-msm-v2" | "qcom,i2c-qup-v2.2.1" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0xc 0x6e 0xd> |
| `interrupt-names` | "qup_irq", "bam_irq" | (absent) |
| `interrupts` | <0x0 0x63 0x0 0x0 0xee 0x0> | <0x0 0x63 0x4> |
| `pinctrl-0` | <0xc7> | <0x83> |
| `pinctrl-1` | <0xc8> | <0x84> |
| `pinctrl-names` | "i2c_active", "i2c_sleep" | "default", "sleep" |
| `qcom,bam-pipe-idx-cons` | <0xc> | (absent) |
| `qcom,bam-pipe-idx-prod` | <0xd> | (absent) |
| `qcom,clk-freq-in` | <0x124f800> | (absent) |
| `qcom,clk-freq-out` | <0x186a0> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,noise-rjct-scl` | <0x0> | (absent) |
| `qcom,noise-rjct-sda` | <0x0> | (absent) |
| `reg` | <0x78b9000 0x600 0x7884000 0x23000> | <0x78b9000 0x500> |
| `reg-names` | "qup_phys_addr", "bam_phys_addr" | (absent) |
| `status` | (absent) | "disabled" |

### `@78ba000` — vendor `i2c@78ba000` / ours `i2c@78ba000`

- vendor 路径 `/soc/i2c@78ba000`
- ours   路径 `/soc@0/i2c@78ba000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,i2c-msm-v2" | "qcom,i2c-qup-v2.2.1" |
| `dma-names` | (absent) | "tx", "rx" |
| `dmas` | (absent) | <0x6e 0xe 0x6e 0xf> |
| `interrupt-names` | "qup_irq", "bam_irq" | (absent) |
| `interrupts` | <0x0 0x64 0x0 0x0 0xee 0x0> | <0x0 0x64 0x4> |
| `pinctrl-0` | <0xc9> | <0x87> |
| `pinctrl-1` | <0xca> | <0x88> |
| `pinctrl-names` | "i2c_active", "i2c_sleep" | "default", "sleep" |
| `qcom,bam-pipe-idx-cons` | <0xe> | (absent) |
| `qcom,bam-pipe-idx-prod` | <0xf> | (absent) |
| `qcom,clk-freq-in` | <0x124f800> | (absent) |
| `qcom,clk-freq-out` | <0x61a80> | (absent) |
| `qcom,master-id` | <0x56> | (absent) |
| `qcom,noise-rjct-scl` | <0x0> | (absent) |
| `qcom,noise-rjct-sda` | <0x0> | (absent) |
| `reg` | <0x78ba000 0x1000 0x7884000 0x23000> | <0x78ba000 0x500> |
| `reg-names` | "qup_phys_addr", "bam_phys_addr" | (absent) |

### `@78d9000` — vendor `usb@78d9000` / ours `usb@78d9000`

- vendor 路径 `/soc/usb@78d9000`
- ours   路径 `/soc@0/usb@78d9000`

| 属性 | vendor | ours |
|---|---|---|
| `HSUSB_1p8-supply` | <0xa8> | (absent) |
| `HSUSB_3p3-supply` | <0xa9> | (absent) |
| `adp-disable` | (absent) | (empty) |
| `ahb-burst-config` | (absent) | <0x0> |
| `compatible` | "qcom,hsusb-otg" | "qcom,ci-hdrc" |
| `dr_mode` | (absent) | "peripheral" |
| `extcon` | (absent) | <0x8c> |
| `hnp-disable` | (absent) | (empty) |
| `hsusb_vdd_dig-supply` | <0x43> | (absent) |
| `interrupt-names` | "core_irq", "async_irq" | (absent) |
| `interrupts` | <0x0 0x86 0x0 0x0 0x8c 0x0> | <0x0 0x86 0x4 0x0 0x8c 0x4> |
| `phy-names` | (absent) | "usb-phy" |
| `phy_type` | (absent) | "ulpi" |
| `phys` | (absent) | <0x8b> |
| `qcom,bus-clk-rate` | <0x17d78400 0xbebc200 0x5f5e100> | (absent) |
| `qcom,dp-manual-pullup` | (empty) | (absent) |
| `qcom,hsusb-otg-mode` | <0x1> | (absent) |
| `qcom,hsusb-otg-otg-control` | <0x2> | (absent) |
| `qcom,hsusb-otg-phy-init-seq` | <0x44 0x80 0x6b 0x81 0x24 0x82 0x13 0x83 0xffffffff> | (absent) |
| `qcom,hsusb-otg-phy-type` | <0x2> | (absent) |
| … | 另有 10 条 | |

### `@b000000` — vendor `interrupt-controller@b000000` / ours `interrupt-controller@b000000`

- vendor 路径 `/soc/interrupt-controller@b000000`
- ours   路径 `/soc@0/interrupt-controller@b000000`

| 属性 | vendor | ours |
|---|---|---|
| `interrupts` | (absent) | <0x1 0x0 0xf04> |
| `reg` | <0xb000000 0x1000 0xb002000 0x1000> | <0xb000000 0x1000 0xb002000 0x2000 0xb001000 0x1000 0xb004000 0x2000> |

### `@86300000` — vendor `qcom,smem@86300000` / ours `smem@86300000`

- vendor 路径 `/soc/qcom,smem@86300000`
- ours   路径 `/reserved-memory/smem@86300000`

| 属性 | vendor | ours |
|---|---|---|
| `hwlocks` | (absent) | <0x2 0x3> |
| `no-map` | (absent) | (empty) |
| `qcom,mpu-enabled` | (empty) | (absent) |
| `qcom,rpm-msg-ram` | (absent) | <0x3> |
| `reg` | <0x86300000 0x100000 0xb011008 0x4 0x60000 0x8000 0x193d000 0x8> | <0x0 0x86300000 0x0 0x100000> |
| `reg-names` | "smem", "irq-reg-base", "aux-mem1", "smem_targ_info_reg" | (absent) |

### `@60150` — vendor `qcom,rpm-master-stats@60150` / ours `sram@60000`

- vendor 路径 `/soc/qcom,rpm-master-stats@60150`
- ours   路径 `/soc@0/sram@60000`

| 属性 | vendor | ours |
|---|---|---|
| `compatible` | "qcom,rpm-master-stats" | "qcom,rpm-msg-ram" |
| `qcom,master-offset` | <0x1000> | (absent) |
| `qcom,master-stats-version` | <0x2> | (absent) |
| `qcom,masters` | "APSS", "MPSS", "PRONTO" | (absent) |
| `reg` | <0x60150 0x2030> | <0x60000 0x8000> |

### `@7824000` — vendor `sdhci@07824000` / ours `mmc@7824900`

- vendor 路径 `/soc/sdhci@07824000`
- ours   路径 `/soc@0/mmc@7824900`

| 属性 | vendor | ours |
|---|---|---|
| `bus-width` | (absent) | <0x8> |
| `compatible` | "qcom,sdhci-msm" | "qcom,msm8916-sdhci", "qcom,sdhci-msm-v4" |
| `interrupts` | <0x0 0x7b 0x0 0x0 0x8a 0x0> | <0x0 0x7b 0x4 0x0 0x8a 0x4> |
| `mmc-ddr-1_8v` | (absent) | (empty) |
| `non-removable` | (absent) | (empty) |
| `pinctrl-0` | <0xac 0xad 0xae> | <0x67> |
| `pinctrl-1` | <0xaf 0xb0 0xb1> | <0x68> |
| `pinctrl-names` | "active", "sleep" | "default", "sleep" |
| `qcom,bus-bw-vectors-bps` | <0x0 0x61a80 0x1312d00 0x17d7840 0x2faf080 0x5f5e100 0xbebc200 0xffffffff> | (absent) |
| `qcom,bus-speed-mode` | "HS200_1p8v", "DDR_1p8v" | (absent) |
| `qcom,bus-width` | <0x8> | (absent) |
| `qcom,cpu-dma-latency-us` | <0x2bd> | (absent) |
| `qcom,msm-bus,name` | "sdhc1" | (absent) |
| `qcom,msm-bus,num-cases` | <0x8> | (absent) |
| `qcom,msm-bus,num-paths` | <0x1> | (absent) |
| `qcom,msm-bus,vectors-KBps` | <0x4e 0x200 0x0 0x0 0x4e 0x200 0x640 0xc80 0x4e 0x200 0x13880 0x27100 0x4e 0x200 0x186a0 0x30d40 0x4e 0x200 0x | (absent) |
| `qcom,nonremovable` | (empty) | (absent) |
| `qcom,vdd-always-on` | (empty) | (absent) |
| `qcom,vdd-current-level` | <0x1f40 0x61a80> | (absent) |
| `qcom,vdd-io-always-on` | (empty) | (absent) |
| … | 另有 9 条 | |

### `@7864000` — vendor `sdhci@07864000` / ours `mmc@7864900`

- vendor 路径 `/soc/sdhci@07864000`
- ours   路径 `/soc@0/mmc@7864900`

| 属性 | vendor | ours |
|---|---|---|
| `bus-width` | (absent) | <0x4> |
| `compatible` | "qcom,sdhci-msm" | "qcom,msm8916-sdhci", "qcom,sdhci-msm-v4" |
| `interrupt-map` | <0x0 0x1 0x0 0x7d 0x0 0x1 0x1 0x0 0xdd 0x0> | (absent) |
| `interrupt-map-mask` | <0xffffffff> | (absent) |
| `interrupts` | <0x0 0x1> | <0x0 0x7d 0x4 0x0 0xdd 0x4> |
| `pinctrl-0` | <0xb2 0xb3 0xb4> | <0x6a> |
| `pinctrl-1` | <0xb5 0xb6 0xb7> | <0x6b> |
| `pinctrl-names` | "active", "sleep" | "default", "sleep" |
| `qcom,bus-bw-vectors-bps` | <0x0 0x61a80 0x1312d00 0x17d7840 0x2faf080 0x5f5e100 0xbebc200 0xffffffff> | (absent) |
| `qcom,bus-width` | <0x4> | (absent) |
| `qcom,cpu-dma-latency-us` | <0x2bd> | (absent) |
| `qcom,msm-bus,name` | "sdhc2" | (absent) |
| `qcom,msm-bus,num-cases` | <0x8> | (absent) |
| `qcom,msm-bus,num-paths` | <0x1> | (absent) |
| `qcom,msm-bus,vectors-KBps` | <0x51 0x200 0x0 0x0 0x51 0x200 0x640 0xc80 0x51 0x200 0x13880 0x27100 0x51 0x200 0x186a0 0x30d40 0x51 0x200 0x | (absent) |
| `qcom,nonremovable` | (empty) | (absent) |
| `qcom,vdd-current-level` | <0x3a98 0x61a80> | (absent) |
| `qcom,vdd-io-current-level` | <0xc8 0xc350> | (absent) |
| `qcom,vdd-io-voltage-level` | <0x1b7740 0x2d0370> | (absent) |
| `qcom,vdd-voltage-level` | <0x2ab980 0x2d0370> | (absent) |
| … | 另有 5 条 | |

## vendor 有、我们没有的节点

按子系统分组。**不代表都要补** —— coresight、camera、adsp-loader 这类是下游专有，主线没有对应驱动，缺了是正常的。

### USB（2 个带地址节点）

- `/soc/qcom,usbbam@78c4000`
  `qcom,usb-bam-msm`
- `/soc/android_usb@086000c8`
  `qcom,android-usb`

### 网络（2 个带地址节点）

- `/soc/qcom,wcnss-wlan@0a000000`
  `qcom,wcnss_wlan`
- `/soc/qcom,pronto@a21b000`
  `qcom,pil-tz-generic`

### 音频（1 个带地址节点）

- `/soc/qcom,spmi@200f000/qcom,pm8916@1/msm8x16_wcd_codec@f100`
  `qcom,wcd-spmi`

### 电源/PMIC（68 个带地址节点）

- `/soc/qcom,gdsc@184c018`
  `qcom,gdsc`  status="okay"
- `/soc/qcom,gdsc@184d078`
  `qcom,gdsc`  status="okay"
- `/soc/qcom,gdsc@185701c`
  `qcom,gdsc`  status="okay"
- `/soc/qcom,gdsc@1858034`
  `qcom,gdsc`  status="okay"
- `/soc/qcom,gdsc@185901c`
  `qcom,gdsc`  status="okay"
- `/soc/qcom,gdsc@184c028`
  `qcom,gdsc`  status="disabled"
- `/soc/qcom,gdsc@184c030`
  `qcom,gdsc`  status="disabled"
- `/soc/tsens@4a8000`
  `qcom,msm8916-tsens`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,revid@100`
  `qcom,qpnp-revid`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/mpps/mpp@a100`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/mpps/mpp@a200`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/mpps/mpp@a300`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/gpios/gpio@c100`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/gpios/gpio@c200`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/gpios/gpio@c300`
  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,pm8916_rtc/qcom,pm8916_rtc_alarm@6100`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@5`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@30`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@31`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@36`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@32`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3100/chan@3c`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3400`
  `qcom,qpnp-adc-tm`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/vadc@3400/chan@30`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,charger/qcom,bat-if@1200`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,charger/qcom,chg-misc@1600`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,vmbms/qcom,batt-pres-status@1208`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,vmbms/qcom,qpnp-chg-pres@1008`
- `/soc/qcom,spmi@200f000/qcom,pm8916@0/qcom,leds@a300`
  `qcom,leds-qpnp`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1400`
  `qcom,qpnp-regulator`  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1400/qcom,ctl@1400`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1400/qcom,ps@1500`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1400/qcom,freq@1600`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1700`
  `qcom,qpnp-regulator`  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1700/qcom,ctl@1700`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1700/qcom,ps@1800`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1700/qcom,freq@1900`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1a00`
  `qcom,qpnp-regulator`  status="disabled"
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1a00/qcom,ctl@1a00`
- `/soc/qcom,spmi@200f000/qcom,pm8916@1/regulator@1a00/qcom,ps@1b00`
- …另有 28 个

### 时钟/复位（1 个带地址节点）

- `/soc/qcom,clock-a7@0b011050`
  `qcom,clock-a53-8916`

### IOMMU/中断（24 个带地址节点）

- `/soc/qcom,iommu@1f00000`
  `qcom,msm-smmu-v2`, `qcom,msm-mmu-500`  status="ok"
- `/soc/qcom,iommu@1f00000/qcom,iommu-ctx@1f09000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1f00000/qcom,iommu-ctx@1f0a000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000`
  `qcom,msm-smmu-v2`, `qcom,msm-mmu-500`  status="ok"
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e22000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e23000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e24000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e25000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e26000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e27000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e28000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e29000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e32000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e33000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e34000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e35000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e36000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e37000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e38000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e39000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e3a000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e3b000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e3c000`
  `qcom,msm-smmu-v2-ctx`
- `/soc/qcom,iommu@1e00000/qcom,iommu-ctx@1e3d000`
  `qcom,msm-smmu-v2-ctx`

### I2C/SPI（2 个带地址节点）

- `/soc/qcom,ispif@1b0a000`
  `qcom,ispif-v3.0`, `qcom,ispif`
- `/soc/i2c@78b9000/synaptics@20`
  status="disabled"

### GPU/视频（1 个带地址节点）

- `/soc/qcom,venus@1de0000`
  `qcom,pil-tz-generic`

### 摄像头（6 个带地址节点）

- `/soc/qcom,csiphy@1b0b000`
  `qcom,csiphy-v3.1`, `qcom,csiphy`
- `/soc/qcom,csid@1b08000`
  `qcom,csid-v3.1`, `qcom,csid`
- `/soc/qcom,csid@1b08400`
  `qcom,csid-v3.1`, `qcom,csid`
- `/soc/qcom,cpp@1b04000`
  `qcom,cpp`
- `/soc/qcom,cci@1b0c000/qcom,actuator@6e`
  `qcom,actuator`
- `/soc/qcom,cci@1b0c000/qcom,actuator@36`
  `qcom,actuator`

### 调试/追踪（20 个带地址节点）

- `/soc/funnel@869000`
  `arm,coresight-funnel`
- `/soc/funnel@868000`
  `arm,coresight-funnel`
- `/soc/csr@801000`
  `qcom,coresight-csr`
- `/soc/cti@812000`
  `arm,coresight-cti`
- `/soc/cti@813000`
  `arm,coresight-cti`
- `/soc/cti@814000`
  `arm,coresight-cti`
- `/soc/cti@815000`
  `arm,coresight-cti`
- `/soc/cti@816000`
  `arm,coresight-cti`
- `/soc/cti@817000`
  `arm,coresight-cti`
- `/soc/cti@818000`
  `arm,coresight-cti`
- `/soc/cti@830000`
  `arm,coresight-cti`
- `/soc/cti@835000`
  `arm,coresight-cti`
- `/soc/cti@838000`
  `arm,coresight-cti`
- `/soc/cti@83c000`
  `arm,coresight-cti`
- `/soc/fuse@5e01c`
  `arm,coresight-fuse-v2`
- `/soc/hwevent@86c000`
  `qcom,coresight-hwevent`
- `/soc/qpdi@1941000`
  `qcom,coresight-qpdi`
- `/soc/qcom,cc-debug@1874000`
  `qcom,cc-debug-8916`
- `/soc/jtagfuse@5e01c`
  `qcom,jtag-fuse`
- `/soc/qseecom@8e700000`
  `qcom,qseecom`  status="okay"

### CPU/拓扑（1 个带地址节点）

- `/soc/qcom,cpu-sleep-status@b088008`
  `qcom,cpu-sleep-status`

### 内存/保留区（6 个带地址节点）

- `/soc/qcom,ion/qcom,ion-heap@25`
- `/soc/qcom,ion/qcom,ion-heap@21`
- `/soc/qcom,ion/qcom,ion-heap@27`
  `qcom,msm-ion-reserve`
- `/soc/qcom,ion/qcom,ion-heap@28`
  `qcom,msm-ion-reserve`
- `/soc/qcom,ion/qcom,ion-heap@23`
  `qcom,msm-ion-reserve`
- `/soc/qcom,ion/qcom,ion-heap@26`
  `qcom,msm-ion-reserve`

### 其它（16 个带地址节点）

- `/soc/qcom,vfe@1b10000`
  `qcom,vfe40`
- `/soc/qcom,jpeg@1b1c000`
  `qcom,jpeg`
- `/soc/qcom,irqrouter@1b00000`
  `qcom,irqrouter`
- `/soc/qcom,mpm2-sleep-counter@4a3000`
  `qcom,mpm2-sleep-counter`
- `/soc/qcrypto@720000`
  `qcom,qcrypto`  status="okay"
- `/soc/qcedev@720000`
  `qcom,qcedev`  status="okay"
- `/soc/qcom,wdt@b017000`
  `qcom,msm-watchdog`
- `/soc/tz-log@8600720`
  `qcom,tz-log`  status="okay"
- `/soc/qcom,msm-imem@8600000`
  `qcom,msm-imem`
- `/soc/qcom,msm-imem@8600000/mem_dump_table@10`
  `qcom,msm-imem-mem_dump_table`
- `/soc/qcom,msm-imem@8600000/restart_reason@65c`
  `qcom,msm-imem-restart_reason`
- `/soc/qcom,msm-imem@8600000/boot_stats@6b0`
  `qcom,msm-imem-boot_stats`
- `/soc/qcom,msm-imem@8600000/pil@94c`
  `qcom,msm-imem-pil`
- `/soc/qcom,spm@b012000`
  `qcom,spm-v2`
- `/soc/qcom,mpm@601d0`
  `qcom,mpm-v2`
- `/soc/qcom,pm@8600664`
  `qcom,pm`

## 我们有、vendor 没有的节点

通常是上游新增的框架节点（opp-table、power-domain、iommu 上下文等），或是 Android 不需要的东西。

- **SIM/Modem**（2）：`@4` service, `@86800000` mpss
- **网络**（1）：`@a204000` remoteproc
- **显示**（1）：`@1a01000` display-controller
- **音频**（3）：`@7702000` sound, `@7708000` audio-controller, `@771c000` audio-codec
- **电源/PMIC**（4）：`@e` channel, `@f` channel, `@290000` sram, `@4a9000` thermal-sensor
- **时钟/复位**（1）：`@b016000` clock
- **IOMMU/中断**（4）：`@2000` iommu-ctx, `@3000` iommu-ctx, `@1ef0000` iommu, `@1f08000` iommu
- **I2C/SPI**（2）：`@78b5000` i2c, `@78b5000` spi
- **调试/追踪**（5）：`@4` port, `@850000` debug, `@852000` debug, `@854000` debug, `@856000` debug
- **内存/保留区**（7）：`@80000000` memory, `@86000000` tz-apps, `@86400000` hypervisor, `@86500000` tz, `@86680000` reserved, `@86700000` rmtfs, `@867e0000` rfsa
- **其它**（19）：`@d0` base1, `@d0` s0-p1, `@d1` s0-p2, `@d2` s1-p1, `@d2` s1-p2, `@d3` s2-p1, `@d4` s2-p2, `@d4` s4-p1, `@d5` s4-p2, `@d5` s5-p1, `@d6` s5-p2, `@d7` base2 …

