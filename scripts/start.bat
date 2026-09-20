@echo off
REM ===================================================================
REM  start.bat - launch the CMIS development server (Windows)
REM  Any arguments are passed through to start.py, e.g.
REM      start.bat --port 8080
REM ===================================================================
setlocal
cd /d "%~dp0\.."

if not exist ".venv" (
    echo No virtual environment found.
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python start.py %*

if errorlevel 1 (
    echo.
    echo The server exited with an error.
    pause
)
endlocal
