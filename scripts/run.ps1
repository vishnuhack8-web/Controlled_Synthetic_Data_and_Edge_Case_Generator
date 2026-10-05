# PowerShell startup script for the SynthEdge AI Platform
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting SynthEdge AI Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "[INFO] Backend API + dashboard: http://localhost:8000" -ForegroundColor Green

python -m backend.main
