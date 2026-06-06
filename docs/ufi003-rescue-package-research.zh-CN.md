# UFI003_MB_V02 救砖包线索

当前真机 PCB 丝印为 `UFI003_MB_V02`。设备曾经使用错误救砖包恢复，目前 Android 能启动但 `getprop` 显示 `UFI001C/ZX_UFI001C`，因此现有 Android 固件只能作为“错包能启动”的证据，不能作为原厂身份依据。

## 目标包

优先寻找：

- `UFI003_MB_V02_EDL.7z`
- `UFI003_MB_V02.zip`
- `UFI003.zip`
- 包内应包含 `rawprogram0.xml`、`patch0.xml`、programmer/firehose 文件和各分区镜像。

找到后先做离线检查，不直接刷：

1. 记录来源 URL、文件名、大小、SHA-256。
2. 解压后列出 `rawprogram0.xml` 中的分区名和镜像文件。
3. 对比当前 ADB 备份的分区布局。
4. 优先只读验证 9008/EDL 能 `printgpt` 或读取分区。
5. 不写 `modemst1/modemst2/fsg/persist`，除非明确要恢复校准且已有本机备份。

## 已知线索

| 来源 | 线索 |
| --- | --- |
| IHEXON UFI001C 平台记录 | 作者的板子丝印同为 `UFI003_MB_V02`，文中提到原厂固件 `UFI003_MB_V02_EDL.7z`，并给出 sha1：`86226dce4f2782dfaa91bc0002317e4cb2cb7693`。 |
| 阿影源码 UFI003 教程 | 文中照片/描述指向 `UFI003_MB_V02`，提到配套资源中 Debian 包对应 `UFI003.zip`，开启 ADB 的固件对应 `UFI003_MB_V02.zip`，并通过 `rawprogram0.xml` 写入。 |
| DuckXu 高通随身 WiFi 记录 | 作者以 `影腾 ufi003_mb_v02` 为例，说明 9008 下 XML 包选择 `rawprogram0.xml`，BIN 包使用 emmc block0 flasher；文章给出工具/驱动 123pan 链接 `https://www.123pan.com/s/PauCjv-l88Jv.html`，以及“遥控车固件”链接 `https://www.123pan.com/s/XwVDVv-WICn3`。 |
| 苏苏小亮亮/Debian 转载链路 | 多个转载页面给出 `https://www.123pan.com/s/XwVDVv-WICn3#1234`，主要是 Debian/OpenWrt/遥控车固件目录；DuckXu 说明可在其中 `Debian-20220608` 目录下载 `UFI003.zip`。这更像 Linux 刷机包，不一定是原厂 Android EDL 包。 |
| 博客园救砖记录 | 文章记录 9008 + miko 全量恢复流程，给出“miko 备份的全量包”链接 `https://www.123pan.com/s/NCtmjv-zRLav.html`，提取码 `1188`；同时给出 miko 工具和驱动链接。文章未明确板型，需要下载后核验。 |
| GitHub gist 讨论 | 有人提到从 123pan 找到 `UFI003.zip`，评论中的设备信息包含 `HW Version: HW1.3`、`SW Version: UFI_003_V01_ZX_DD_221215`、`Baseband: UFI003_CT 20220903`。 |
| ufiClub 文章列表 | 有 `高通410棒子(UFI003_MB_V02)刷机包分享(持续更新)` 条目，但当前停止注册，暂时不能作为可获取来源。 |

## 候选下载入口

| 链接 | 可能内容 | 风险/备注 |
| --- | --- | --- |
| `https://www.123pan.com/s/PauCjv-l88Jv.html` | DuckXu 汇总的工具、驱动和可能的 UFI003_MB_V02 相关刷机资料。 | 需要人工打开确认目录和提取码；不要直接运行不明工具。 |
| `https://www.123pan.com/s/XwVDVv-WICn3#1234` | 苏苏小亮亮/遥控车固件目录，公开转载较多；可能含 `Debian-20220608/UFI003.zip`。 | 主要用于 Debian/OpenWrt，不能当作原厂救砖包。 |
| `https://www.123pan.com/s/8y49-LwZ0h` | GitHub gist 和多个转载提到的酷铵水遍/MIKO 刷机包来源。 | 可能需要注册或网盘客户端；先只下载、列目录、算 hash。 |
| `https://www.123pan.com/s/NCtmjv-zRLav.html` 提取码 `1188` | 博客园文章给出的 miko 备份全量包，作者称约 3GB，可恢复分区表。 | 文章未说明具体型号，必须下载后对比 `rawprogram0.xml`、分区大小、boot/system 证据。 |
| `https://www.123pan.com/s/NCtmjv-eRLav.html` 提取码 `1188` | 博客园文章给出的 miko 工具链接。 | 只作为工具来源线索，不在本仓库运行。 |
| `https://www.123pan.com/s/NCtmjv-LRLav.html` 提取码 `1188` | 博客园文章给出的 9008/Qualcomm 驱动链接。 | 只作为驱动来源线索。 |
| `https://pan.baidu.com/s/11YNVZPSMbX0zo9oaxyuFQQ` 提取码 `is4d` | 数码之家帖子补发链接。 | 内容未知，需离线核验，不可信任为原厂包。 |

## 已下载包离线检查

`D:\123pan\Downloads\ufi003_mb_v02影腾原厂包.zip`

- SHA-256：`30c313ae5d136f1a5da8a8561490f135b807286b9358800239800b491c90572d`
- 本地分析目录：`out/firmware-packages/ufi003_mb_v02-yingteng-stock/`
- 包内有 `backup/rawprogram0.xml`、`patch0.xml`、`partition.xml`、GPT、`NON-HLOS.bin`、`boot.img`、`recovery.img`、`system.img`、`userdata.img`、`persist.img` 和 bootloader 链镜像。
- `rawprogram0.xml` 分区大小和当前 ADB 备份布局基本一致；`userdata` 使用 `num_partition_sectors=0`，由 `patch0.xml` 动态吃剩余空间。
- 包内 `system.img` 可搜到 build properties，版本为 `2022-05-21`，仍包含 `ro.build.model_type=ZX_UFI001C` 和 `ro.build.cust_proj=UFI001C`，所以它不是一个干净标识为 UFI003 的 Android 系统镜像。
- 包内 `boot.img` 不是标准 Android boot image 魔数，但含 `UFI003_CT 20211210` 字符串；需要确认这是否为工具导出的特殊分区格式或文件名混淆。
- 包内关键镜像和当前错包 ADB 备份 hash 不同，说明不是当前运行的 `2022-06-15` 错包。

高风险点：

- `rawprogram0.xml` 中 `abootbak` 的 `filename` 是 `boot.img`，疑似异常；正常情况下更可能应为 `emmc_appsboot.mbn`。不能盲刷原始 XML。
- 包会写 `modemst1`、`modemst2`、`fsg`、`persist`。这些包含校准/设备个体数据，除非明确要恢复且已有本机备份，否则应从刷写列表中剔除。
- 包会写 GPT。虽然布局匹配当前机器，但首次验证建议只读 EDL，并优先准备“修正/裁剪后的 rawprogram”，不要直接全盘恢复。

## MIKO 全盘 bin 包检查

分析目录：

```text
out/firmware-packages/miko-full-images/
out/firmware-packages/remote-onepkg/
```

当前设备 ADB 看到的 `mmcblk0` 大小约 `3702784 KiB`，即 `3791650816` bytes。MIKO 全盘 bin 是否可用于本机整盘恢复，首先要看镜像总长度是否不超过该容量。

| 包 | 解包文件 | 源包 SHA-256 | 解包文件 SHA-256 | 解包文件大小 | 判断 |
| --- | --- | --- | --- | --- | --- |
| `3.53G miko包_UFI003.bin.7z` | `椰贝003_3.53G miko包.bin` | `6dbe93b08a07464cdf795e0afddd36b30baf4a64800697f2da3d12128e410782` | `dc7dee25b28e69a5c464605735dca05b2bf9dfccd8e335c2795c0dcac3154dc5` | `3791633920` | 最接近当前本机 eMMC 容量；含 GPT、`UFI003_CT 20211210`、Android boot/QCDT/FDT、system build `eng.liufeihua.20220507`。当前最有价值的 UFI003 全盘候选。 |
| `3.61G_miko003.7z` | `003.bin` | `2ed2e8749fcf16b31d9a9d822eb368172af327800bee943e0f224dc9eb6ac8bd` | `196d4fceaee8d02ab360a319282ee60f4021269ac0dc51ed929bbd95bfe8d74a` | `3875520000` | 含 `UFI003_CT 20211210` 和 `UFI003_MB_V02.qcn`，但镜像大于当前本机 eMMC 容量约 80 MiB；不能作为本机整盘直写候选。 |
| `MIKO-QRZL903-1.zip` | `QRZL903-1.bin` | `b2f23bb42db3a777c604666e8ecd2269d2447f35284534cc959cd91845caf1d6` | `8fb0b9b078ab646d5ffbf97abdaadac76f2743fce0329352c6cab8b592442fda` | `3875520000` | 标记为 `UFI001CT 20211106`，QCN 也含 `UFI001C`；不是 UFI003_MB_V02 候选。 |

补充：

- `3.61G_miko003.7z` 附带 `UFI003_MB_V02.qcn`，SHA-256：`bbcd4fb4aa709a6c196278ecd90f7cb4c27cddb63cdcf4e54f4b46b0c692945e`。QCN 内含 `UFI003_CT 20211210`。
- `MIKO-QRZL903-1.zip` 附带 `QRZL903-1.qcn`，SHA-256：`f4926fd44398127926af7f36cd277907d2e455f3a569955733ef46feaf8eb659`。QCN 内含 `UFI001CT 20211106`。
- 三个 bin 都有 GPT，分区名和当前设备一致：`modem`、`sbl1`、`aboot`、`rpm`、`tz`、`hyp`、`modemst1/2`、`fsg`、`boot`、`system`、`persist`、`cache`、`recovery`、`userdata`。
- 即使 `3.53G` 容量匹配，也不建议直接整盘写入，因为会覆盖本机 `modemst1`、`modemst2`、`fsg`、`persist` 等个体校准/持久化数据。更安全的方式是从该全盘 bin 中按 GPT 偏移切出 `boot/system/recovery` 等分区，或只作为离线对比和最终救砖兜底。

## 当前本机证据

本地备份路径：

```text
out/bringup/410-android/
```

已有：

- `firmware/partitions/`：ADB root 只读备份的关键分区。
- `firmware/partitions/SHA256SUMS`：备份校验和。
- `reports/scanned-dtbs.tar.gz`：当前 boot 中抽出的 33 个 DTB。
- `reports/selected-dtb-04-512mb-mtp.dts`：当前运行匹配的 MSM 8916 512MB MTP DTS。

注意：这些来自错包系统，只能用于恢复当前“能启动状态”和比对分区布局，不能替代 UFI003_MB_V02 原厂包。

## 参考链接

- IHEXON 记录：https://ihexon.github.io/2023/10/21/ufimakefun.html
- 阿影源码教程：https://www.ayym.net/post-4918.html
- DuckXu 记录：https://i.duckxu.com/archives/play_qualcomm_410_wifi_hotspot_stick_to_debian_and_openwrt_with_adb_on.html
- 苏苏小亮亮刷机转载：https://blog.csdn.net/molun1101/article/details/127961397
- 博客园救砖记录：https://www.cnblogs.com/Iterworld/p/17779673.html
- GitHub gist 讨论：https://gist.github.com/185264646/cb13f3216b45dd75e13fdf579bfcf623
- ufiClub 文章列表：https://www.mywifi.bond/articles
