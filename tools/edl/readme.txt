MSM8916 (UFI003-02) EDL 刷机说明
============================================================

本包内已自带刷机所需的一切：edl.exe、firehose loader、刷机脚本。
不需要安装 Python，不需要装 fastboot，解压后双击脚本即可。

------------------------------------------------------------
一、包内文件说明
------------------------------------------------------------
  flash_edl_original.bat    首次完整刷机（备份 NV + lk1st + boot + rootfs）
  flash_edl_secondary.bat   二次刷机（只更新 boot + rootfs）
  lk1st-msm8916.mbn         一级引导（刷入 aboot 分区）
  boot.img                  内核 + initramfs
  <设备名>.img              rootfs（刷入 userdata 分区）
  README_edl.txt            本说明
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
   - 下载并运行 Zadig（https://zadig.akeo.ie/）
   - Options -> List All Devices
   - 下拉框选择 "QHSUSB_BULK" 或 "QDLoader 9008"
   - 目标驱动选 "WinUSB"
   - 点 "Install Driver"（已装过则点 "Replace Driver"）

3. 验证：设备管理器里该设备不再有黄色感叹号。

注意：绝对不要用 qcusbser.sys 之类的串口驱动，必须是 WinUSB。

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
  edl.exe /l<loader>                               加载 programmer
  edl.exe /r /pmodem   backup\modem_backup.bin     备份 modem
  edl.exe /r /ppersist backup\persist_backup.bin   备份 persist
  edl.exe /w /paboot lk1st-msm8916.mbn             写 aboot（lk1st）
  edl.exe /w /pboot boot.img                       写 boot
  edl.exe /w /puserdata <设备名>.img               写 userdata
  edl.exe /z                                       重启

NV 备份会存到脚本同目录的 backup\ 下，请自行保存好。

【重要】本脚本不重建 GPT 分区表。如果设备原分区表里
userdata 容量不足以容纳 rootfs 镜像，写 userdata 会失败或截断。
这种情况需要先单独处理分区表，再刷 rootfs。

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
六、已知 MSM8916 分区（供参考，实际以 /g 输出为准）
------------------------------------------------------------
  aboot      1MB      bootloader（lk1st 刷这里）
  boot       32MB     内核 + initramfs
  userdata   ~2.6GB   pmOS rootfs（整个系统）
  system     ~850MB   通常不使用
  recovery   16MB
  cache      128MB
  persist    32MB     NV 数据，必须备份
  modem      64MB     Modem 固件，必须备份
  sbl1       512KB
  rpm        512KB
  tz         512KB
  hyp        512KB
  fsg        1.5MB
  DDR        32KB

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

------------------------------------------------------------
八、参考
------------------------------------------------------------
  Temblast EDL Utility: https://github.com/bkerler/edl
  postmarketOS MSM8916:  https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_410/412_(MSM8916)
  lk2nd:                 https://github.com/msm8916-mainline/lk2nd
