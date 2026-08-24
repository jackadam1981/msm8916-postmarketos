@echo off
echo ==========================================
echo EDL 二次刷机
echo ==========================================
echo 请确保设备已连接 EDL 模式 (Vol Down + USB)
echo.
echo 步骤 1: 刷入 boot.img
if exist out\boot.img (
    fastboot edl flash boot out\boot.img
    echo boot.img 刷入成功
) else (
    echo 错误: 未找到 boot.img
)
echo.
echo 步骤 2: 刷入 rootfs
if exist out\410stick-ufi003-mb-v02.img (
    fastboot edl flash userdata out\410stick-ufi003-mb-v02.img
    echo rootfs 刷入成功
) else (
    echo 错误: 未找到 410stick-ufi003-mb-v02.img
)
echo.
echo ==========================================
echo 二次刷机脚本完成
echo ==========================================
pause