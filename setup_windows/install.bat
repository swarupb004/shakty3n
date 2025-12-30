@echo off
REM Shakty3n Windows Installation Script
REM =====================================

echo ============================================
echo   Shakty3n - Autonomous Agentic Coder
echo   Windows Installation Script
echo ============================================
echo.

REM Ensure we run from the repository root
cd /d "%~dp0.."

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check Python version
echo Checking Python version...
python --version

REM Check if pip is available
where pip >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip is not installed!
    echo Please ensure pip is installed with Python.
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
python -m pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo To start, run the following commands:
echo.
echo   1. Configure your API keys:
echo      python shakty3n.py configure
echo.
echo   2. Test connection:
echo      python shakty3n.py test --provider openai
echo.
echo   3. Start the API server:
echo      python shakty3n.py serve
echo.
echo   4. (Optional) Install and run Web UI:
echo      cd platform_web
echo      npm install
echo      npm run dev
echo.
echo For more information, see README.md and QUICKSTART.md
echo.
pause
