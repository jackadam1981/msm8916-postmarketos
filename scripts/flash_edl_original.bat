@echo off
echo ==========================================
echo EDL 原厂固件刷机
echo ==========================================
echo 请确保设备已连接 EDL 模式 (Vol Down + USB)
echo.
echo 步骤 1: 备份 NV 数据 (modem, persist)
echo fastboot edl dump_modem modem_backup.img
echo fastboot edl dump_persist persist_backup.img
echo.
echo 步骤 2: 重新分区
echo 应用原厂分区表 for UFI003-02
echo.
echo 步骤 3: 恢复 NV 数据
echo fastboot edl restore_modem modem_backup.img
echo fastboot edl restore_persist persist_backup.img
echo.
echo 步骤 4: 刷入 lk1st bootloader
if exist out\lk1st-msm8916.mbn (
    fastboot edl flash lk1st out\lk1st-msm8916.mbn
    echo lk1st 刷入成功
) else (
    echo 错误: 未找到 lk1st-msm8916.mbn
    echo 请确保已构建 full compile 模式
)
echo.
echo 步骤 5: 刷入 boot.img
if exist out\boot.img (
    fastboot edl flash boot out\boot.img
    echo boot.img 刷入成功
) else (
    echo 错误: 未找到 boot.img
)
echo.
echo 步骤 6: 刷入 rootfs
if exist out\410stick-ufi003-mb-v02.img (
    fastboot edl flash userdata out\410stick-ufi003-mb-v02.img
    echo rootfs 刷入成功
) else (
    echo 错误: 未找到 410stick-ufi003-mb-v02.img
)
echo.
echo ==========================================
echo 原厂固件刷机脚本完成
echo ==========================================
pause