@echo off
REM Run Auto Import Now - Chạy import ngay lập tức
REM ================================================

echo.
echo ========================================
echo   CGV Import Now
echo ========================================
echo.
echo Running import immediately...
echo.

cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

REM Run import now
python scripts\ophim_import_v3.py --run-now

pause
