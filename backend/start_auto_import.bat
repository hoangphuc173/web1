@echo off
REM Auto Import - Tự động import phim 2 lần mỗi ngày (12:00 và 00:00)
REM ================================================================

echo.
echo ========================================
echo   CGV Auto Import Scheduler
echo ========================================
echo.
echo Starting auto-import service...
echo Schedule: Daily at 12:00 and 00:00
echo.

cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

REM Run the auto-import script
python scripts\ophim_import_v3.py --auto

pause
