@echo off
setlocal enabledelayedexpansion
title MSM8916 pmOS - Second Flash (EDL)

rem ============================================================
rem  MSM8916 (UFI003-02) second flash: update boot + rootfs only
rem  Tool: Temblast EDL Utility (edl\edl.exe)
rem  Usage: keep this .bat, edl\ folder and images in same dir,
rem         then double-click this file.
rem ============================================================

cd /d "%~dp0"

set "EDL=%~dp0edl\edl.exe"
rem ---- auto pick firehose loader (official DB410c first) ----
set "LOADER="
for %%f in ("%~dp0edl\prog_emmc_firehose_8916.mbn" "%~dp0edl\prog_emmc_firehose_8916_gucci_peek.mbn") do (
    if not defined LOADER if exist "%%~ff" set "LOADER=%%~ff"
)
set "BOOT=%~dp0boot.img"
set "ROOTFS="

rem ---- auto find rootfs image ----
rem  --split emits <device>-boot.img (the 512 MiB /boot partition) next to
rem  <device>-root.img.  Both end in .img, and "-boot.img" sorts first, so
rem  excluding only the literal name "boot.img" would put the /boot
rem  partition on userdata.  Prefer the root image by name.
set "ROOTFS="
for %%f in ("%~dp0*-root.img") do (
    if not defined ROOTFS if exist "%%~ff" set "ROOTFS=%%~ff"
)
if not defined ROOTFS for %%f in ("%~dp0*ufi003*.img" "%~dp0*rootfs*.img" "%~dp0*.img") do (
    if not defined ROOTFS if exist "%%~ff" (
        set "CAND=%%~nxf"
        if /i not "!CAND!"=="boot.img" if /i not "!CAND:~-9!"=="-boot.img" (
            set "ROOTFS=%%~ff"
        )
    )
)

echo ============================================================
echo   MSM8916 pmOS - Second Flash (boot + rootfs)
echo ============================================================
echo   EDL tool : %EDL%
echo   Loader   : %LOADER%
echo   boot.img : %BOOT%
echo   rootfs   : %ROOTFS%
echo ============================================================
echo   NOTE: This script assumes the NEW GPT is already in place.
echo         If you are flashing a brand-new device, use
echo         flash_edl_original.bat instead (it repartitions).
echo ============================================================
echo.

rem ---- pre-checks ----
if not exist "%EDL%" (
    echo [ERROR] edl\edl.exe not found
    echo         Keep the edl folder next to this script.
    pause & exit /b 1
)
if not exist "%LOADER%" (
    echo [ERROR] firehose loader not found in edl\
    pause & exit /b 1
)
if not exist "%BOOT%" (
    echo [ERROR] boot.img not found
    pause & exit /b 1
)
if not defined ROOTFS (
    echo [ERROR] rootfs image *.img not found
    pause & exit /b 1
)
if not exist "%ROOTFS%" (
    echo [ERROR] rootfs image missing: %ROOTFS%
    pause & exit /b 1
)

echo Put the device into EDL mode (9008):
echo   1. Power off completely
echo   2. Hold Volume Down
echo   3. Plug in USB
echo   4. Device Manager shows "Qualcomm HS-USB QDLoader 9008"
echo.
echo [WARNING] This overwrites boot and userdata partitions.
echo           All data in userdata will be lost.
echo.
choice /c YN /m "Continue flashing"
if errorlevel 2 (
    echo Cancelled.
    pause & exit /b 0
)
echo.

rem ---- step 1: load firehose programmer ----
echo [1/4] Loading firehose programmer...
"%EDL%" /l"%LOADER%"
if errorlevel 1 (
    echo       Load returned error - if device is already in firehose
    echo       mode this is harmless, continuing.
)
echo.

rem ---- step 2: write boot ----
echo [2/4] Writing boot.img to boot partition...
"%EDL%" /w /pboot "%BOOT%"
if errorlevel 1 (
    echo [FAILED] boot.img write failed
    echo          Check: WinUSB driver installed? device in 9008 mode?
    pause & exit /b 1
)
echo       boot.img written OK
echo.

rem ---- step 3: write rootfs ----
echo [3/4] Writing rootfs to userdata partition (large file, be patient)...
"%EDL%" /w /puserdata "%ROOTFS%"
if errorlevel 1 (
    echo [FAILED] rootfs write failed
    pause & exit /b 1
)
echo       rootfs written OK
echo.

rem ---- step 4: reset ----
echo [4/4] Rebooting device...
"%EDL%" /z
echo.

echo ============================================================
echo   Flash complete
echo ============================================================
echo   If the device does not boot, check UART (ttyMSM0 115200).
echo   To restore the stock system use flash_edl_original.bat.
echo.
pause
endlocal
