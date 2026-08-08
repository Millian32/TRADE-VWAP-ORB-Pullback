[CmdletBinding()]
param(
    [string]$Symbol,
    [string]$Timeframe,
    [Nullable[int]]$PollSeconds,
    [Nullable[int]]$MaxLoops
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

if ($null -eq $PollSeconds) {
    $PollSeconds = 5
}
if ($null -eq $MaxLoops) {
    $MaxLoops = 0
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run .\setup.ps1 first."
}

$parts = @("auto_trader.py", "--dry-run", "--broker-name", "paper", "--poll-seconds", "$PollSeconds")

if ($Symbol) {
    $parts += @("--symbol", $Symbol)
}
if ($Timeframe) {
    $parts += @("--timeframe", $Timeframe)
}
if ($MaxLoops -gt 0) {
    $parts += @("--max-loops", "$MaxLoops")
}

Write-Host "Starting paper dry-run trader..."
& .\.venv\Scripts\python.exe $parts
