@echo off
title RNDIS 一键自动驱动
echo 正在卸载冲突驱动...
pnputil /remove-driver oem67.inf /uninstall /force /yes 2>nul
echo 正在安装微软官方 RNDIS 驱动...
pnputil /add-driver netrndis.inf /install 2>nul
echo 正在安装高通兼容驱动...
pnputil /add-driver oem67.inf /install 2>nul
echo 正在重新扫描硬件变更...
pnputil /enum-devices /refresh >nul
echo.
echo ==========================================
echo 操作完成！请拔掉 USB 设备
echo 重新插入 USB 设备，Windows 将自动完成驱动安装
echo （约需 10-30 秒）
echo ==========================================
pause