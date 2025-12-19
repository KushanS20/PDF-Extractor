@echo off
echo ===================================================
echo DEBUG MODE - INVOICE EXTRACTOR
echo ===================================================
echo.

echo 1. Checking Python Version...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found. Please install Python.
    pause
    exit /b
)
echo.

echo 2. Installing Dependencies...
echo Upgrading pip...
python -m pip install --upgrade pip
echo Installing requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo Please fix the errors above.
    pause
    exit /b
)
echo.

echo 3. Starting Flask Backend (Test Mode)...
echo Press CTRL+C to stop this test after 5 seconds if it starts successfully.
echo.
python app.py
pause
