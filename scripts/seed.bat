@echo off
REM ===================================================================
REM  seed.bat - load fictional demo data into the database (Windows)
REM ===================================================================
setlocal
cd /d "%~dp0\.."

if not exist ".venv" (
    echo No virtual environment found. Run setup.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python manage.py seed_demo

echo.
echo Demo accounts ^(password: Demo@12345^):
echo   superadmin  admin  pastor  finance  youthleader  member1
echo.
pause
endlocal
