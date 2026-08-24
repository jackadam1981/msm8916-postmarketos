EDL 工具中文说明
============================

1. 前置要求 (必读)
--------------------
• 必须安装 Windows 驱动程序 (WinUSB) - 否则脚本将无法运行
• 推荐使用 Zadig 工具进行驱动安装
• 必须了解如何进入 EDL 模式

2. 安装 WinUSB 驱动 (必须步骤)
--------------------------------
1. 进入 EDL 模式:
   - 设备关机
   - 按住音量下键 (Vol Down)
   - 同时插入 USB 线缆
   - 等待几秒钟，LED 指示灯可能会亮起或设备会振动

2. 使用 Zadig 安装驱动:
   - 运行: tools\edl\src\bkerler-edl\Drivers\Windows\zadig-2.8.exe
   - 在下拉框中选择你的设备 (QHSUSB_BULK)
   - 选择 "WinUSB" 作为内核驱动
   - 点击 "Install Driver"
   - 如果提示 "WinUSB already installed", 点击 "Replace Driver"

3. 在 设备管理器 中验证:
   - 应该能看到 "USB Serial Device" 或 "QDLoader 9008" 配有 WinUSB
   - 如果出现黄色警告图标，需要重新安装驱动

3. 原厂固件完整刷机流程
--------------------------------
此流程用于设备首次刷机或恢复出厂设置，包含以下步骤：

第一步：备份 NV 数据 (modem, persist)
- 连接 EDL 模式下的设备
- 使用 EDL 工具读取并备份 modem 分区
- 读取并备份 persist 分区
- 将备份文件保存至电脑安全位置

第二步：重新分区
- 应用 UFI003-02 (MSM8916) 的原厂分区表
- 使用 fastboot 或 EDL 工具重新设置分区大小和类型
- 确保以下分区正确创建：
  • system (~850MB - EFI System partition)
  • userdata (~2.6GB - User data / 内部存储)
  • recovery (16MB - 恢复分区)
  • cache (128MB - 缓存分区)
  • persist (32MB - persist 分区)
  • modem (64MB - Modem/Baseband 固件)
  • 以及其他必要分区 (sbl1, aboot, rpm, tz, hyp, fsg 等)

第三步：恢复 NV 数据
- 将第一步备份的 modem 数据恢复回设备
- 将第一步备份的 persist 数据恢复回设备
- 验证数据是否成功写入

第四步：刷入 lk1st bootloader
- 使用包含的 flash_edl_original.bat 脚本
- 或手动执行: fastboot edl flash lk1st out\lk1st-msm8916.mbn
- 确认 lk1st 刷入成功

第五步：刷入 boot.img
- 使用脚本或手动: fastboot edl flash boot out\boot.img
- 确认 boot.img 刷入成功

第六步：刷入 rootfs
- 使用脚本或手动: fastboot edl flash userdata out\410stick-ufi003-mb-v02.img
- 确认 rootfs 刷入成功

第七步：重启验证
- 执行重启: fastboot edl reboot
- 观察设备是否正常启动
- 检查是否进入 pmOS 系统或恢复界面

4. 二次刷机流程
--------------------------------
此流程用于已刷过原厂固件的设备，仅更新 pmOS 组件，流程更简洁：

第一步：刷入 boot.img
- 连接 EDL 模式下的设备
- 执行: fastboot edl flash boot out\boot.img
- 或运行 flash_edl_secondary.bat 脚本
- 确认 boot.img 刷入成功

第二步：刷入 rootfs
- 继续执行: fastboot edl flash userdata out\410stick-ufi003-mb-v02.img
- 或脚本自动完成
- 确认 rootfs 刷入成功

第三步：重启验证
- 执行重启: fastboot edl reboot
- 等待设备启动 pmOS 系统
- 验证系统是否正常工作

5. 二次刷机注意事项
--------------------------------
• 仅刷入 boot 和 rootfs，不重新分区
• 不备份/恢复 NV 数据 (modem, persist)
• 适用于已经拥有原厂固件的设备
• 如果出现问题，可能需要恢复至原厂固件再进行完整刷机

6. 常用命令
--------------------------------
• printgpt - 读取 GPT 分区表 (推荐第一步)
• r userdata out\userdata_current.bin - 读取 userdata 分区
• rs 0 80000000 out\emmc_full.img - 读取完整 eMMC 镜像
• w userdata out\userdata_to_write.bin - 写入分区 (谨慎使用，可能导致设备变砖)

6. 已知 MSM8916 分区 (来自 printgpt 输出)
--------------------------------
• system: ~850MB (EFI System partition)
• userdata: ~2.6GB (User data / 内部存储)
• recovery: 16MB (Recovery partition)
• cache: 128MB (Cache partition)
• persist: 32MB (persist partition)
• modem: 64MB (Modem/ Baseband firmware)
• sbl1: 512KB (Bootloader SBL1)
• aboot: 1MB (ABOOT - boot image)
• rpm: 512KB (RPM - 实时处理器)
• tz: 512KB (TZ - Trustzone)
• hyp: 512KB (Hypervisor)
• fsg: 1.5MB (File Storage Group)
• DDR: 32KB (DDR 培训数据)
• ... (总计 ~20+ 个分区)

6. 故障排除
--------------------------------
如遇错误：

1. "NotImplementedError: Operation not supported or unimplemented on this platform"
   - DRIVER NOT INSTALLED - 按上文说明安装 WinUSB 驱动
   - 永远不要使用 qcusbser.sy - 始终使用通过 Zadig 安装的 WinUSB

2. Device not found / "Waiting for the device" 永久挂起
   - 确认正确的 EDL 模式: Vol Down + Power + USB 连接
   - 尝试不同的 USB 端口 (推荐 USB 2.0，而非 USB 3.0 集线器)
   - 尝试不同的 USB 数据线 (质量很重要，必须支持模式切换)
   - 重新安装驱动 (先卸载，后重新安装)

3. "Host's payload to target size is too large" (正常，忽略)
   - 这是 firehose client 的非致命警告
   - 脚本将在该消息后正常继续

4. Access denied / 权限错误
   - 以管理员身份运行 CMD/PowerShell
   - 右键终端 -> "以管理员身份运行"

7. 参考链接
--------------------------------
• 原始 edlclient: https://github.com/bkerler/edl
• MSM8916 设备: Qualcomm Snapdragon 410 (MSM8916)
• 驱动来源: tools\edl\src\bkerler-edl\Drivers\Windows\
• Last updated: 2026

===============
使用说明
===============
1. 确保已安装 WinUSB 驱动 (参见第2节)
2. 将设备置于 EDL 模式 (参见第2节第1步)
3. 运行脚本:
   - Windows: 双击 flash_edl_original.bat (原厂固件) 或 flash_edl_secondary.bat (二次刷机)
   - 或使用 tools\edl\run-edl.bat 配合命令
4. 按照脚本提示完成刷机过程
5. 重启设备并验证是否正常工作