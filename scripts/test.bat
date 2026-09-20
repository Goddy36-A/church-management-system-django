@echo off
REM ===================================================================
REM  test.bat - run Django system checks and the test suite (Windows)
REM ===================================================================
setlocal
cd /d "%~dp0\.."

if not exist ".venv" (
    echo No virtual environment found. Run setup.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Running system checks...
python manage.py check
if errorlevel 1 goto :done

echo.
echo Running test suite...
python manage.py test

:done
echo.
pause
endlocal
