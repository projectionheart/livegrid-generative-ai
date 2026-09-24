@echo off
setlocal
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%~dp0..\..\work\venv\Scripts\python.exe"
"%PY%" app.py --calibration
pause
