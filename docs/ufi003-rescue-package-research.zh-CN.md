# UFI003_MB_V02 救砖包线索

当前真机 PCB 丝印为 `UFI003_MB_V02`。设备曾经使用错误救砖包恢复，目前 Android 能启动但 `getprop` 显示 `UFI001C/ZX_UFI001C`，因此现有 Android 固件只能作为“错包能启动”的证据，不能作为原厂身份依据。

## 目标包

优先寻找：

- `UFI003_MB_V02_EDL.7z`
- `UFI003_MB_V02.zip`
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
| GitHub gist 讨论 | 有人提到从 123pan 找到 `UFI003.zip`，评论中的设备信息包含 `HW Version: HW1.3`、`SW Version: UFI_003_V01_ZX_DD_221215`、`Baseband: UFI003_CT 20220903`。 |
| ufiClub 文章列表 | 有 `高通410棒子(UFI003_MB_V02)刷机包分享(持续更新)` 条目，但内容需要登录。 |

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
- GitHub gist 讨论：https://gist.github.com/185264646/cb13f3216b45dd75e13fdf579bfcf623
- ufiClub 文章列表：https://www.mywifi.bond/articles
