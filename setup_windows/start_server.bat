@echo off
REM Shakty3n - Start API Server
REM ============================

echo Starting Shakty3n API Server...
echo.

cd /d "%~dp0.."
python shakty3n.py serve --host 0.0.0.0 --port 8000

pause
