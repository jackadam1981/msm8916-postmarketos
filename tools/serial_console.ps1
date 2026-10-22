#Requires -Version 5.1
<#
.SYNOPSIS
    One-shot serial console session runner for the MSM8916 stick.

.DESCRIPTION
    Opens the CH340 UART once, optionally logs in, runs a list of commands
    (read from a UTF-8 file, one per line), then dumps everything received.

    Keeping the whole session inside a single open/close cycle is required:
    the pmOS getty drops the login state if the port is closed and reopened.

.PARAMETER Port
    Serial port name, default COM5.

.PARAMETER CmdFile
    Text file with one shell command per line. Lines starting with # are skipped.

.PARAMETER User
    Login user. Empty string skips the login sequence.

.PARAMETER Pass
    Login password.

.PARAMETER Raw
    Skip the login sequence and just send the commands as-is.

.EXAMPLE
    powershell -File tools/serial_console.ps1 -CmdFile out/cmds.txt
#>
param(
    [string]$Port   = "COM5",
    [int]$Baud      = 115200,
    [string]$CmdFile,
    [string]$User   = "pmos",
    [string]$Pass   = "pmos",
    [switch]$Raw,
    [switch]$NoReset,
    [int]$WakeMs    = 1200,
    [int]$UserMs    = 1500,
    [int]$PassMs    = 5000,
    [int]$CmdMs     = 3500,
    [int]$TailMs    = 4000
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CmdFile)) { throw "command file not found: $CmdFile" }

$cmds = Get-Content -Path $CmdFile -Encoding UTF8 |
        ForEach-Object { $_.TrimEnd() } |
        Where-Object { $_.Length -gt 0 -and -not $_.StartsWith("#") }

if (-not [System.IO.Ports.SerialPort]::GetPortNames() -contains $Port) {
    throw "serial port $Port not present. Replug the CH340 or check the driver."
}

$sp = New-Object System.IO.Ports.SerialPort $Port, $Baud, "None", 8, "One"
$sp.Handshake    = [System.IO.Ports.Handshake]::None
$sp.DtrEnable    = $true
$sp.RtsEnable    = $true
$sp.ReadTimeout  = 500
$sp.WriteTimeout = 2000
$sp.NewLine      = "`r"

function Read-For {
    param([int]$Ms)
    $buf = New-Object System.Text.StringBuilder
    $deadline = (Get-Date).AddMilliseconds($Ms)
    while ((Get-Date) -lt $deadline) {
        try {
            $chunk = $sp.ReadExisting()
            if ($chunk) { [void]$buf.Append($chunk) }
        } catch { }
        Start-Sleep -Milliseconds 60
    }
    return $buf.ToString()
}

try {
    $sp.Open()
} catch {
    Start-Sleep -Milliseconds 2000
    $sp.Open()
}

$log = New-Object System.Text.StringBuilder

# Pager jail escape. nmcli/journalctl/man all page through less on a tty, and a
# session that ended inside a pager swallows every later keystroke. Send quit +
# interrupt a few times so the shell is reachable again.
if (-not $NoReset) {
    # NB: PowerShell 5.1 has no `u{} escape, so build the control chars explicitly.
    $ctrlC = [string][char]3
    $ctrlZ = [string][char]26
    foreach ($k in @("q", "q", $ctrlC, $ctrlC, $ctrlZ)) {
        try { $sp.Write($k) } catch { }
        Start-Sleep -Milliseconds 400
    }
    [void]$log.Append((Read-For -Ms 800))
}

try {
    if (-not $Raw) {
        # Wake the console and log in.
        $sp.Write("`r")
        [void]$log.Append((Read-For -Ms $WakeMs))

        $sp.Write("$User`r")
        [void]$log.Append((Read-For -Ms $UserMs))

        $sp.Write("$Pass`r")
        [void]$log.Append((Read-For -Ms $PassMs))
    }

    foreach ($c in $cmds) {
        $sp.Write("$c`r")
        [void]$log.Append((Read-For -Ms $CmdMs))
    }

    [void]$log.Append((Read-For -Ms $TailMs))
}
finally {
    try { $sp.Close() } catch { }
    $sp.Dispose()
}

# Strip the ANSI escapes the pmOS shell loves, then print.
$text = $log.ToString()
$text = $text -replace "`e\[[0-9;?]*[a-zA-Z]", ""
$text = $text -replace "`e\][^`a]*`a", ""
$text
