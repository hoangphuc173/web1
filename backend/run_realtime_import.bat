@echo off
echo ===============================================
echo  OPHIM FAST IMPORT - REAL-TIME MODE
echo ===============================================
echo.
echo This will import new movies every 5 MINUTES
echo (More frequent updates for real-time experience)
echo Press Ctrl+C to stop
echo.
echo Starting...
echo.

cd /d "%~dp0..\.."
python backend\scripts\ophim_import_v3.py --continuous --interval 5 --check-update

pause
