@echo off
setlocal enabledelayedexpansion
title MSM8916 pmOS - Full Flash (EDL)

rem ============================================================
rem  MSM8916 (UFI003-02) full flash with NEW partition table:
rem    backup NV -> write GPT -> lk1st(aboot) -> boot -> persist -> rootfs
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

rem ---- GPT images ----
set "GPT_MAIN=%~dp0gpt_pmos_main.bin"
set "GPT_BACK=%~dp0gpt_pmos_backup.bin"

echo ============================================================
echo   MSM8916 pmOS - Full Flash (with new partition table)
echo ============================================================
echo   EDL tool : %EDL%
echo   Loader   : %LOADER%
echo   lk1st    : %LK1ST%
echo   boot.img : %BOOT%
echo   rootfs   : %ROOTFS%
echo   backup   : %BKDIR%
echo   GPT main : %GPT_MAIN%
echo   GPT back : %GPT_BACK%
echo ============================================================
echo.

rem ---- pre-checks ----
if not exist "%EDL%"    ( echo [ERROR] edl\edl.exe not found & pause & exit /b 1 )
if not exist "%LOADER%" ( echo [ERROR] firehose loader not found in edl\ & pause & exit /b 1 )
if not exist "%LK1ST%"  ( echo [ERROR] lk1st-msm8916.mbn not found & pause & exit /b 1 )
if not exist "%BOOT%"   ( echo [ERROR] boot.img not found & pause & exit /b 1 )
if not defined ROOTFS   ( echo [ERROR] rootfs image *.img not found & pause & exit /b 1 )
if not exist "%GPT_MAIN%" ( echo [ERROR] gpt_pmos_main.bin not found & pause & exit /b 1 )
if not exist "%GPT_BACK%" ( echo [ERROR] gpt_pmos_backup.bin not found & pause & exit /b 1 )

echo Put the device into EDL mode (9008):
echo   1. Power off completely
echo   2. Hold Volume Down
echo   3. Plug in USB
echo   4. Device Manager shows "Qualcomm HS-USB QDLoader 9008"
echo.
echo [WARNING] This will REPARTITION the eMMC and overwrite
echo           aboot, boot and userdata.  All Android data
echo           will be lost.  NV backups are made first.
echo.
choice /c YN /m "Continue full flash"
if errorlevel 2 (
    echo Cancelled.
    pause & exit /b 0
)
echo.

rem ---- step 1: load programmer ----
echo [1/8] Loading firehose programmer...
"%EDL%" /l"%LOADER%"
if errorlevel 1 (
    echo       Load returned error - if device is already in firehose
    echo       mode this is harmless, continuing.
)
echo.

rem ---- step 2: backup NV partitions ----
echo [2/8] Backing up NV partitions (modem / persist)...
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

rem ---- step 3: write new GPT ----
echo [3/8] Writing new partition table (primary + backup GPT)...
echo         boot expanded to 32 MiB, persist moved, userdata enlarged.
"%EDL%" /w /s0 /c34 "%GPT_MAIN%"
if errorlevel 1 (
    echo [FAILED] Primary GPT write failed
    pause & exit /b 1
)
echo       Primary GPT written OK
"%EDL%" /w /s7405535 /c33 "%GPT_BACK%"
if errorlevel 1 (
    echo [FAILED] Backup GPT write failed
    pause & exit /b 1
)
echo       Backup GPT written OK
echo       NOTE: a new edl.exe process will now pick up the new table.
echo.

rem ---- step 4: write lk1st to aboot ----
echo [4/8] Writing lk1st to aboot partition...
"%EDL%" /w /paboot "%LK1ST%"
if errorlevel 1 (
    echo [FAILED] lk1st write failed
    pause & exit /b 1
)
echo       lk1st written OK
echo.

rem ---- step 5: write boot ----
echo [5/8] Writing boot.img to boot partition...
"%EDL%" /w /pboot "%BOOT%"
if errorlevel 1 (
    echo [FAILED] boot.img write failed
    pause & exit /b 1
)
echo       boot.img written OK
echo.

rem ---- step 6: restore persist to new location ----
echo [6/8] Restoring persist to new location (moved by new GPT)...
if exist "%BKDIR%\persist_backup.bin" (
    "%EDL%" /w /ppersist "%BKDIR%\persist_backup.bin"
    if errorlevel 1 (
        echo       [WARN] persist restore failed - device may boot without
        echo                calibration data (WiFi/BT MAC may be random)
    ) else (
        echo       persist restored OK
    )
) else (
    echo       [SKIP] persist backup not found - skipping restore
    echo              (WiFi/BT MAC may be random on first boot)
)
echo.

rem ---- step 7: write rootfs ----
echo [7/8] Writing rootfs to userdata partition (large file, be patient)...
"%EDL%" /w /puserdata "%ROOTFS%"
if errorlevel 1 (
    echo [FAILED] rootfs write failed
    pause & exit /b 1
)
echo       rootfs written OK
echo.

rem ---- step 8: reset ----
echo [8/8] Rebooting device...
"%EDL%" /z
echo.

echo ============================================================
echo   Full flash complete
echo ============================================================
echo.
echo   If the device does not boot, check UART (ttyMSM0 115200).
echo   NV backups are in the backup\ folder - keep them safe.
echo.
pause
endlocal
