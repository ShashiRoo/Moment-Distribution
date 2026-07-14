@echo off
title Hardy Cross Beam Solver
echo ===================================================
echo   🏗️ Hardy Cross Continuous Beam Solver Launcher
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH.
    echo Please install Python and ensure "Add Python to PATH" is checked.
    echo.
    pause
    exit /b
)

:: Change directory to where this batch file is located
cd /d "%~dp0"

echo [INFO] Booting Streamlit server...
echo [INFO] The solver will open automatically in your browser at http://127.0.0.1:8501
echo.
python -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1

pause
