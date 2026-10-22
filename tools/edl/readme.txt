MSM8916 (UFI003-02) EDL 刷机说明
============================================================

本包内已自带刷机所需的一切：edl.exe、firehose loader、刷机脚本。
不需要安装 Python，不需要装 fastboot，解压后双击脚本即可。

------------------------------------------------------------
一、包内文件说明
------------------------------------------------------------
  gpt_pmos_main.bin         新 GPT 主表（34 扇区）
  gpt_pmos_backup.bin       新 GPT 备份表（33 扇区）
  rawprogram0.xml           高通 rawprogram 格式参考（GPT 写入用）
  flash_edl_original.bat    首次完整刷机（备份 NV + 写 GPT + lk1st + boot + rootfs）
  flash_edl_secondary.bat   二次刷机（只更新 boot + rootfs，假设 GPT 已改好）
  lk1st-msm8916.mbn         一级引导（刷入 aboot 分区）
  boot.img                  内核 + initramfs
  <设备名>.img              rootfs（刷入 userdata 分区）
                            必须是纯 ext4 文件系统，不是整盘镜像，见第七节第 7 条
  README_edl.txt            本说明
  zadig-2.9.exe             WinUSB 驱动安装工具（装驱动用，见第二节）
  edl\edl.exe               Temblast Qualcomm EDL Utility
  edl\prog_emmc_firehose_8916.mbn              官方 DB410c firehose
  edl\prog_emmc_firehose_8916_gucci_peek.mbn   小米 gucci firehose（备用）

脚本会自动在 edl\ 下查找 loader，优先用第一个，找不到才用第二个。

------------------------------------------------------------
二、第一步：安装 WinUSB 驱动（只需做一次）
------------------------------------------------------------
1. 让设备进入 EDL 模式：
   - 设备完全关机
   - 按住音量下键不放
   - 插入 USB 线
   - 设备管理器出现 "Qualcomm HS-USB QDLoader 9008"（可能带黄色感叹号）

2. 安装 WinUSB 驱动：
   - 运行包内的 zadig-2.9.exe（不需要联网，也不用去官网下）
   - Options -> List All Devices
   - 下拉框选择 "QHSUSB_BULK" 或 "QDLoader 9008"
   - 目标驱动选 "WinUSB"
   - 点 "Install Driver"（已装过则点 "Replace Driver"）

3. 验证：设备管理器里该设备不再有黄色感叹号。

注意 1：绝对不要用 qcusbser.sys 之类的串口驱动，必须是 WinUSB。

注意 2：Zadig 的目标驱动下拉框里有 WinUSB / libusb-win32 / libusbK 三个选项。
        选成后两个也能"安装成功"，但 edl.exe 只认 WinUSB，会一直报
        "Could not find EDL device"，而且不会有任何提示告诉你是驱动选错了。
        这是整个刷机流程里最容易卡死的地方，务必确认选的是 WinUSB。

注意 3：如果设备已经装过 Qualcomm 的串口驱动（设备管理器里显示成 COM 口
        而不是 9008），先用 Zadig 把它替换成 WinUSB。

------------------------------------------------------------
三、刷机：二次刷机（已刷过 lk1st 的设备）
------------------------------------------------------------
适用场景：设备已经能跑 pmOS/lk1st，只想更新内核或系统。

  1. 设备进 EDL 模式（见第二节）
  2. 双击 flash_edl_secondary.bat
  3. 确认提示后等待完成（rootfs 较大，需要几分钟）
  4. 设备自动重启

脚本执行的实际命令：
  edl.exe /l<loader>                       加载 firehose programmer
  edl.exe /w /pboot boot.img               写 boot 分区
  edl.exe /w /puserdata <设备名>.img       写 userdata 分区
  edl.exe /z                               重启

------------------------------------------------------------
四、刷机：首次完整刷机（新设备 / 恢复）
------------------------------------------------------------
适用场景：第一次刷 pmOS，或设备已变砖需要重建。

  1. 设备进 EDL 模式（见第二节）
  2. 双击 flash_edl_original.bat
  3. 确认提示后等待完成
  4. 设备自动重启

脚本执行的实际命令：
  edl.exe /l<loader>                                      加载 programmer
  edl.exe /r /pmodem   backup\modem_backup.bin            备份 modem
  edl.exe /r /ppersist backup\persist_backup.bin          备份 persist
  edl.exe /w /s0 /c34 gpt_pmos_main.bin                   写新 GPT 主表
  edl.exe /w /s7405535 /c33 gpt_pmos_backup.bin           写新 GPT 备份表
  edl.exe /w /paboot lk1st-msm8916.mbn                    写 aboot（lk1st）
  edl.exe /w /pboot boot.img                              写 boot
  edl.exe /w /ppersist backup\persist_backup.bin          恢复 persist（新位置）
  edl.exe /w /puserdata <设备名>.img                      写 userdata
  edl.exe /z                                              重启

NV 备份会存到脚本同目录的 backup\ 下，请自行保存好。

新 GPT 把 boot 扩大到 32MB（原 16MB 装不下 22MB 的 boot.img），
把 persist 搬到 boot 后面，userdata 从 2.4GB 扩大到 3.3GB。
persist 的内容会在备份后自动写回新位置，不需要手动算偏移。

------------------------------------------------------------
五、手动执行（脚本失败时排查用）
------------------------------------------------------------
在解压目录打开 CMD（Shift + 右键 -> 在此处打开 PowerShell/CMD）：

  edl\edl.exe /i
      读设备信息，确认能连上（连不上就是驱动或 EDL 模式问题）

  edl\edl.exe /g
      打印 GPT 分区表，确认 boot / aboot / userdata 分区名存在

  edl\edl.exe /l"edl\prog_emmc_firehose_8916.mbn"
      只加载 programmer，验证 loader 是否可用

  edl\edl.exe /w /pboot boot.img
      单独写 boot 分区

  edl\edl.exe /r /pmodem backup\modem.bin
      单独读某分区

  edl\edl.exe /z
      重启设备（/zo 关机，/zf 进 fastboot，/ze 回 EDL）

完整参数列表：edl\edl.exe /?

------------------------------------------------------------
六、已知 MSM8916 分区（新 GPT，供参考，实际以 /g 输出为准）
------------------------------------------------------------
  aboot      1MB      bootloader（lk1st 刷这里）
  boot       32MB     内核 + initramfs（原 16MB，已扩大）
  userdata   ~3.3GB   pmOS rootfs（原 2.4GB，已扩大）
  persist    32MB     NV 数据，必须备份（已搬到新位置）
  modem      64MB     Modem 固件，必须备份
  sbl1       512KB    二级引导（ Qualcomm 启动链第二环，不动）
  rpm        512KB    电源管理固件（控制 CPU 频率/电压/休眠，不动）
  tz         512KB    TrustZone 安全固件（指纹/DRM/安全存储，不动）
  hyp        512KB    虚拟化管理器（为 lk1st 提供虚拟化支持，不动）
  fsg        1.5MB    工厂校准数据（modem 配套，不动）
  DDR        32KB     内存时序参数（上电初始化 RAM 用，不动）

  system / cache / recovery  已删除，空间合并到 userdata

------------------------------------------------------------
七、故障排除
------------------------------------------------------------
1. "Could not find EDL device"
   - 设备没进 EDL 模式，或驱动没装好
   - 重新插拔，确认设备管理器里有 9008 设备
   - 换 USB 2.0 端口，换质量好的数据线
   - 不要用 USB 3.0 Hub

2. 加载 loader 后报错 / 卡住
   - 换另一个 loader 试：
     edl\edl.exe /l"edl\prog_emmc_firehose_8916_gucci_peek.mbn"

3. 写入时 "Access denied" 或权限错误
   - 右键脚本 -> 以管理员身份运行

4. rootfs 写入失败 / 中途断开
   - userdata 分区容量不足，或数据线不稳
   - 先用 /g 看 userdata 实际大小
   - 检查镜像大小是否超过分区容量

5. 刷完起不来
   - 接 UART（ttyMSM0, 115200）看引导日志
   - 确认 lk1st 和 boot.img 是同一批次构建的
   - 用 flash_edl_original.bat 完整重刷一遍

6. 需要回退原厂系统
   - 用 backup\ 下的 modem/persist 备份恢复 NV
   - 再刷回原厂 boot/aboot/userdata 镜像

7. 刷写成功但开机卡住 / 找不到根文件系统
   - 多半是 rootfs 镜像的格式不对。本包里的 <设备名>.img 必须是
     【一个纯 ext4 文件系统】，不能是"整盘镜像"。
   - 整盘镜像是 pmbootstrap 默认产物，它内部还带一张 GPT 分区表，
     里面分成 boot 和 root 两个区。那是往整块 eMMC 写的，
     塞进 userdata 分区等于在一个分区里再套一层分区表，
     内核自然找不到根文件系统。
   - 怎么分辨：纯 ext4 的镜像，大小通常几百 MB 到 1GB 出头；
     整盘镜像会明显更大（含 boot 分区）。本项目在打包时会自动
     把整盘镜像切成 root 分区，正常发布的包里不该出现这种情况。
   - 如果拿到了这种镜像，可以用仓库里的工具切一下：
       python tools\carve_rootfs.py <设备名>.img -o rootfs.img
     它会把 root 分区取出来并校验确实是 ext4。
   - 校验一个镜像到底是不是 ext4（在解压目录打开 CMD）：
       certutil -dump <设备名>.img | more
     看文件开头：ext4 在偏移 1080 处有 53 EF 两个字节，
     开头没有 55 AA 结尾的 MBR，也没有 "EFI PART" 字样。

------------------------------------------------------------
八、关于 edl.exe 的来源与校验
------------------------------------------------------------
edl.exe 不是本项目的代码，是第三方工具，来源必须说清楚：

  工具名称   Qualcomm EDL Utility
  作者       Temblast
  出处       https://www.temblast.com/edl.htm
  版权       Copyright (c) Temblast 2022-2025
  构建时间   2025-12-27T23:49:17Z（从 exe 版本资源读出）
  许可       闭源免费工具，作者个人网站直接分发，没有公开源码

它【不是】 https://github.com/bkerler/edl 那个项目。
bkerler/edl 是 Python 写的 edl.py，需要装 Python 和 libusb，用法也不同。
网上搜 "edl.exe" 很容易搜到 bkerler 的仓库，两者不是一回事，别混。

本包内三个二进制文件的 SHA256（可用 certutil 核对）：

  edl.exe
    331e02ef38980ca04a7e1e87b0b24cc25be4192f1daf21559900c46ff7515198
  edl\prog_emmc_firehose_8916.mbn
    d80f7bbedf895096c912782ed88bb37cf80418a22187b16143f4bbd25e2b6eb2
  edl\prog_emmc_firehose_8916_gucci_peek.mbn
    081b5fa07a28fd9702a54980a149fd4430e3686eb82e530181571c3f73bc0771

核对方法（在解压目录打开 CMD）：
  certutil -hashfile edl\edl.exe SHA256

关于安全性，需要你知道的事实：

  - edl.exe 是 32 位 Delphi 程序，只调用系统 DLL 和 WINUSB.DLL，
    不依赖任何额外的 DLL，所以包里不需要带 libusb。
  - 它的导入表里没有任何网络相关 DLL（没有 WS2_32 / WININET /
    URLMON / CRYPT32），不会往外传数据。
  - 但它是闭源的，无法逐行审计，而刷机时它需要以管理员权限运行。
    如果你不能接受这个风险，可以改用开源的 bkerler/edl（Python）
    或 qdl（C 语言，BSD 许可），代价是要自己装环境。

------------------------------------------------------------
九、关于 zadig-2.9.exe 的来源与校验
------------------------------------------------------------
zadig-2.9.exe 也不是本项目的代码，是第三方工具：

  工具名称   Zadig
  作者       Pete Batard（公司 Akeo Consulting，爱尔兰）
  出处       https://zadig.akeo.ie/
  开源仓库   https://github.com/pbatard/libwdi
  版本       2.9.788
  构建时间   2024-06-13T12:54:27Z（从 PE 头读出）
  许可       GPL v3
  版权       (c) 2010-2023 Pete Batard

和 edl.exe 最大的区别：Zadig 是开源软件，而且是【有代码签名的】。

  签名者     CN=Akeo Consulting, O=Akeo Consulting, S=Donegal, C=IE
  颁发者     CN=Sectigo Public Code Signing CA EV R36
  时间戳     CN=Symantec SHA256 TimeStamping Signer - G3
  验证结果   签名有效

签名证书本身在 2024-09-29 到期，但因为带 RFC3161 时间戳，签名依然有效
（Windows 会按签名时刻的证书状态来判定）。你可以自己验证：

  PowerShell:
    Get-AuthenticodeSignature .\zadig-2.9.exe | Format-List

  或右键 zadig-2.9.exe -> 属性 -> 数字签名，应该能看到 Akeo Consulting。

SHA256：
  zadig-2.9.exe
    4ecaa95df3da3621486a043aef8b3050b8bafe7c901402871e816229ef82039b

关于安全性：Zadig 用 libwdi 给设备装 WinUSB 驱动，需要管理员权限，
这是装驱动的固有要求。它是 GPL v3 开源项目，源码在 pbatard/libwdi，
可以自行编译比对。本包内这份是官方 2.9 发行版，未做任何修改。

------------------------------------------------------------
十、参考
------------------------------------------------------------
  Temblast EDL Utility   https://www.temblast.com/edl.htm
  bkerler/edl (Python)   https://github.com/bkerler/edl
  Zadig                  https://zadig.akeo.ie/
  libwdi (Zadig 源码)    https://github.com/pbatard/libwdi
  postmarketOS MSM8916   https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_410/412_(MSM8916)
  lk2nd                  https://github.com/msm8916-mainline/lk2nd
