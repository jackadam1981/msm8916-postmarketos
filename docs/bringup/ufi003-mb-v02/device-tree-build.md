# 设备树构建：从"看着对"到"编译过"

## 为什么要放到 CI 里编

这台开发机是 Windows，`dtc`、`cpp`、`fdtdump`、`fdtget` 一个都没有，
`arm-none-eabi-gcc` 也没有。设备树之前只能靠肉眼和原厂 dtb 对比，从来没有
真正编译过一次。

`.github/workflows/dt-verify.yml` 就是补上这一步。它只做一件事：把 dts 编成
dtb 并对产物做断言，几分钟跑完，不用等 300 分钟的整包构建。

## 这个 workflow 做了什么

1. 从 `config/kernel-testing/.../APKBUILD` 读 `pkgver`，拼出内核 tag
   （当前 `v6.12.1-msm8916`）。不写死版本，内核升级自动跟随。
2. sparse checkout 只拉 `arch/arm64/boot/dts` 和 `include`（完整内核约 2 GB，
   这里只要几十 MB）。
3. `git apply` 同一个 patch —— 和 abuild 的 `default_prepare()` 用一份文件。
4. `cpp` + `dtc`，参数和内核的 `cmd_dtc` 一致。
5. `tools/dtb/verify_dtb.py` 读**编译产物**做断言。
6. `dtb2dts` → `dts2dtb --verify` 往返，回归测试我们自己的工具。
7. 和原厂 dtb 跑一次 `dtb_audit.py` 对照（只输出，不判定）。
8. 上传 dtb 作为 artifact。

## 首次构建结果

| 项目 | 值 |
|---|---|
| 内核 tag | `v6.12.1-msm8916` |
| qcom dts 文件数 | 466 |
| patch 应用 | `git apply` 一次通过 |
| 预处理后行数 | 3,428 |
| **dtb 大小** | **50,361 字节** |
| 节点数 | 443 |
| 断言 | 19 项全过 |
| 往返编译 | 字节一致 |

对比旧的手工 dtb：51,342 字节 / 448 节点。

## 和旧 dtb 的差异（全部有解释）

**少 5 个节点，都是 fixed regulator：**

```
/regulator-usb-v1p8   /regulator-usb-v3p3
/regulator-remoteproc-pll  /regulator-remoteproc-mx  /regulator-remoteproc-cx
```

**remoteproc 换了绑定**：旧的 `cx-supply` / `mx-supply` / `pll-supply` 变成
`power-domains` + `power-domain-names`。这是 6.12 的新写法。旧 dtb 还在用
老绑定，而内核是 6.12.1 —— **mpss 很可能一直没 probe 成功**，调制解调器也就
一直没起来。换内核编出来的 dtb 顺带把这个修掉了。

**eMMC 补了供电**：`vmmc-supply` / `vqmmc-supply` 出现，旧 dtb 没有。

**删掉两个属性**：

- `extcon`（USB 控制器和 PHY 各一处）—— 我们的 dts 显式 `/delete-property/`，
  因为这块板子永远做 device，线缆检测没有意义。
- `qcom,board-id` / `qcom,msm-id` —— 只有 lk2nd 用，我们走 lk1st，不需要。
- `qcom,netdev-channel-mask` —— 下游残留。

其余差异是 phandle 值整体偏移 1（少了一个节点），没有实质影响。

## 关键发现：USB PHY 供电来自 PMIC，不是板级 LDO

旧 dtb 里：

```
/soc@0/usb@78d9000/ulpi/phy
    v1p8-supply = <&regulator_usb_v1p8>   /* regulator-fixed */
    v3p3-supply = <&regulator_usb_v3p3>   /* regulator-fixed */
```

新 dtb（6.12 上游 `msm8916-ufi.dtsi` 的默认值）：

```
    v1p8-supply -> /remoteproc/smd-edge/rpm-requests/regulators/l7
    v3p3-supply -> /remoteproc/smd-edge/rpm-requests/regulators/l13
```

哪个对？查原厂 Android dtb：

```
/soc/usb@78d9000
    HSUSB_1p8-supply  = <0xa8>  ->  /soc/qcom,rpm-smd/rpm-regulator-ldoa7/regulator-l7
                                     regulator-name = "8916_l7"
    HSUSB_3p3-supply  = <0xa9>  ->  /soc/qcom,rpm-smd/rpm-regulator-ldoa13/regulator-l13
                                     regulator-name = "8916_l13"
```

**原厂就是 L7 / L13。** 新 dtb 和硬件一致；旧 dtb 那两个 `regulator-fixed`
是更早内核版本的遗留，只是让这两路电看起来像板级可控，实际上并不能控制。

`verify_dtb.py` 已经把这条固化成断言：PHY 的 `v1p8-supply` 必须落在
`regulators/l7`，`v3p3-supply` 必须落在 `regulators/l13`。

顺带确认：6.12 上游的 `msm8916-thwc-ufi001c.dts` 只有 66 行，根本没有那些
fixed regulator。旧 dtb 不是从 6.12 编出来的。

## 断言清单（19 项）

`tools/dtb/verify_dtb.py` 检查的是会直接影响启动的值，不是风格：

| 检查 | 后果 |
|---|---|
| `model` / `compatible` / `chassis-type` | 板型识别 |
| `memory@80000000` = 512 MiB @ `0x80000000` | 内存容量 |
| `usb` `dr_mode=peripheral`，无 `usb-role-switch` | 做 device 才有 gadget |
| 全树无 `extcon` | 确认删除真的生效 |
| PHY `v1p8`→L7、`v3p3`→L13 | USB 供电 |
| `venus` `disabled` | 无显示、编解码不可用 |
| `mpss` `okay` 且有 `pinctrl-0` | 调制解调器 + SIM mux |
| LED GPIO 20/21/22 | WIFI_S / 4G_L2 / 4G_S |
| 重启键 GPIO 37 | 按键 |
| SIM mux 三组引脚与电平（GPIO 2 为 `output-high`） | 卡检测 |

一个坑：`dtb_dump.render()` 会把短的 cell 数组误判成字符串 ——
重启键的 `<&tlmm 37 GPIO_ACTIVE_HIGH>` 会被渲染成 `['','','','I',...]`。
所以 `verify_dtb.py` 直接 `struct.unpack` 原始字节，不走 `render()`。

## 改 dts 之后怎么重编

```bash
# 1. 改 tools/dtb/msm8916-zhihe-ufi003-mb-v02.dts
# 2. 重新生成 patch（同时打印新的 sha512）
python scripts/pmaports/gen-kernel-dts-patch.py
# 3. 把新 sha512 写进 APKBUILD 的 sha512sums，pkgrel +1
# 4. 推上去，workflow 自动跑（改了 config/kernel-testing/** 就会触发）
```

第 3 步不能忘：patch 变了但 `sha512sums` 没更新，abuild 会在整包构建时
校验失败，而 dt-verify 因为不走 abuild 反而看不出来。

## 已知边界

- 这个 workflow 验证的是**设备树**，不是内核包。整包构建仍然走
  `pmos-build.yml`，那里有 `tar -tzf | grep dtb` 兜底。
- 编译用的 `dtc` 是 Ubuntu 的 `device-tree-compiler`，不是内核自带的
  `scripts/dtc`。两者对本树没有差异（往返字节一致可佐证），但内核若开始用
  新 dtc 特性，这里可能先过、整包构建才报错。
- 断言里的节点路径用后缀匹配，能容忍 `soc@0` → `soc` 这类改名，但节点真的
  被重命名时会失败 —— 那时按报错信息更新即可。
