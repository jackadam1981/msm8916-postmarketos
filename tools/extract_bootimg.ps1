param(
    [Parameter(Mandatory = $true)]
    [string]$InputImage,

    [Parameter(Mandatory = $false)]
    [string]$OutputDirectory = "out/extracted-bootimg"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputImage -PathType Leaf)) {
    throw "Input image does not exist: $InputImage"
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$resolvedInput = Resolve-Path -LiteralPath $InputImage
$resolvedOutput = Resolve-Path -LiteralPath $OutputDirectory

$manifest = @"
InputImage: $resolvedInput
OutputDirectory: $resolvedOutput

Next manual tools to run as available:
- unpackbootimg or magiskboot for boot image splitting
- dtc for DTB to DTS decompilation
- tools/extract_qcom_ids.py for qcom ID extraction
"@

$manifestPath = Join-Path $resolvedOutput "README.txt"
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8

Write-Host "Prepared extraction workspace: $resolvedOutput"
Write-Host "Manifest written: $manifestPath"
