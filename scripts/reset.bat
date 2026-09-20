@echo off
REM ===================================================================
REM  reset.bat - DESTRUCTIVE: wipe the database and reseed it (Windows)
REM ===================================================================
setlocal
cd /d "%~dp0\.."

echo.
echo *******************************************************
echo   WARNING: this deletes ALL data in the database.
echo *******************************************************
echo.
set /p CONFIRM="Type yes to continue: "
if /i not "%CONFIRM%"=="yes" (
    echo Aborted.
    pause
    exit /b 0
)

if not exist ".venv" (
    echo No virtual environment found. Run setup.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python start.py --reset --yes --no-run

echo.
pause
endlocal
