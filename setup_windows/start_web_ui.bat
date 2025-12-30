@echo off
REM Shakty3n - Start Web UI
REM ========================

echo Starting Shakty3n Web UI...
echo.

cd /d "%~dp0..\platform_web"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

npm run dev

pause
