@echo off
setlocal
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%~dp0..\..\work\venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Run Install on Windows.cmd first.
  pause
  exit /b 1
)
start "" "http://127.0.0.1:8765"
"%PY%" app.py
pause
