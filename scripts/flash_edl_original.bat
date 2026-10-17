@echo off
setlocal enabledelayedexpansion
title MSM8916 pmOS - Full Flash (EDL)

rem ============================================================
rem  MSM8916 (UFI003-02) full flash:
rem    backup NV -> lk1st(aboot) -> boot -> rootfs
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
set "LK1ST=%~dp0lk1st-msm8916.mbn"
set "BOOT=%~dp0boot.img"
set "ROOTFS="
set "BKDIR=%~dp0backup"

rem ---- auto find rootfs image (skip boot.img) ----
for %%f in ("%~dp0*ufi003*.img" "%~dp0*rootfs*.img" "%~dp0*.img") do (
    if not defined ROOTFS if exist "%%~ff" (
        if /i not "%%~nxf"=="boot.img" set "ROOTFS=%%~ff"
    )
)

echo ============================================================
echo   MSM8916 pmOS - Full Flash
echo ============================================================
echo   EDL tool : %EDL%
echo   Loader   : %LOADER%
echo   lk1st    : %LK1ST%
echo   boot.img : %BOOT%
echo   rootfs   : %ROOTFS%
echo   backup   : %BKDIR%
echo ============================================================
echo.

rem ---- pre-checks ----
if not exist "%EDL%"    ( echo [ERROR] edl\edl.exe not found & pause & exit /b 1 )
if not exist "%LOADER%" ( echo [ERROR] firehose loader not found in edl\ & pause & exit /b 1 )
if not exist "%LK1ST%"  ( echo [ERROR] lk1st-msm8916.mbn not found & pause & exit /b 1 )
if not exist "%BOOT%"   ( echo [ERROR] boot.img not found & pause & exit /b 1 )
if not defined ROOTFS   ( echo [ERROR] rootfs image *.img not found & pause & exit /b 1 )

echo Put the device into EDL mode (9008):
echo   1. Power off completely
echo   2. Hold Volume Down
echo   3. Plug in USB
echo   4. Device Manager shows "Qualcomm HS-USB QDLoader 9008"
echo.
echo [WARNING] This overwrites aboot, boot and userdata partitions.
echo           All data in userdata will be lost.
echo           NV partitions (modem/persist) are backed up first.
echo.
choice /c YN /m "Continue full flash"
if errorlevel 2 (
    echo Cancelled.
    pause & exit /b 0
)
echo.

rem ---- step 1: load programmer ----
echo [1/6] Loading firehose programmer...
"%EDL%" /l"%LOADER%"
if errorlevel 1 (
    echo       Load returned error - if device is already in firehose
    echo       mode this is harmless, continuing.
)
echo.

rem ---- step 2: backup NV partitions ----
echo [2/6] Backing up NV partitions (modem / persist)...
if not exist "%BKDIR%" mkdir "%BKDIR%"
"%EDL%" /r /pmodem "%BKDIR%\modem_backup.bin"
if errorlevel 1 (
    echo       [WARN] modem backup failed - strongly recommend fixing first
    choice /c YN /m "Continue anyway"
    if errorlevel 2 ( echo Aborted. & pause & exit /b 1 )
) else (
    echo       modem backup OK
)
"%EDL%" /r /ppersist "%BKDIR%\persist_backup.bin"
if errorlevel 1 (
    echo       [WARN] persist backup failed - strongly recommend fixing first
    choice /c YN /m "Continue anyway"
    if errorlevel 2 ( echo Aborted. & pause & exit /b 1 )
) else (
    echo       persist backup OK
)
echo.

rem ---- step 3: write lk1st to aboot ----
echo [3/6] Writing lk1st to aboot partition...
"%EDL%" /w /paboot "%LK1ST%"
if errorlevel 1 (
    echo [FAILED] lk1st write failed
    pause & exit /b 1
)
echo       lk1st written OK
echo.

rem ---- step 4: write boot ----
echo [4/6] Writing boot.img to boot partition...
"%EDL%" /w /pboot "%BOOT%"
if errorlevel 1 (
    echo [FAILED] boot.img write failed
    pause & exit /b 1
)
echo       boot.img written OK
echo.

rem ---- step 5: write rootfs ----
echo [5/6] Writing rootfs to userdata partition (large file, be patient)...
"%EDL%" /w /puserdata "%ROOTFS%"
if errorlevel 1 (
    echo [FAILED] rootfs write failed
    pause & exit /b 1
)
echo       rootfs written OK
echo.

rem ---- step 6: reset ----
echo [6/6] Rebooting device...
"%EDL%" /z
echo.

echo ============================================================
echo   Full flash complete
echo ============================================================
echo   NOTE: this script does NOT rebuild the GPT partition table.
echo         If userdata is smaller than the rootfs image, writing
echo         will fail or truncate. Fix the partition table first.
echo.
echo   If the device does not boot, check UART (ttyMSM0 115200).
echo   NV backups are in the backup\ folder - keep them safe.
echo.
pause
endlocal
