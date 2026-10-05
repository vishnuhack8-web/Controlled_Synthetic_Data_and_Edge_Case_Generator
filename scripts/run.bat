@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%\src"

echo ===================================================
echo   Starting SynthEdge AI Platform
echo ===================================================
echo [INFO] Backend API + dashboard: http://localhost:8000

python -m backend.main
endlocal
