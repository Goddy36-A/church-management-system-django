@echo off
REM ===================================================================
REM  setup.bat - one-time setup for the CMIS Django project (Windows)
REM  Creates a virtualenv, installs dependencies, migrates, and seeds.
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo.
echo ==========================================================
echo   Church Management Information System - Setup
echo ==========================================================
echo.

call :find_python || goto :fail_python

if not exist ".venv" (
    echo [1/4] Creating virtual environment...
    "%PY%" -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        goto :end_fail
    )
) else (
    echo [1/4] Virtual environment already exists - skipping.
)

echo [2/4] Installing dependencies...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    goto :end_fail
)

echo [3/4] Applying database migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Migrations failed.
    goto :end_fail
)

echo [4/4] Seeding demo data...
python manage.py seed_demo
if errorlevel 1 (
    echo WARNING: Seeding failed. The app will still run, but with no demo data.
)

echo.
echo ==========================================================
echo   Setup complete.
echo   Run start.bat to launch the server.
echo.
echo   Demo accounts ^(password: Demo@12345^):
echo     superadmin  admin  pastor  finance  youthleader  member1
echo ==========================================================
echo.
pause
exit /b 0

:find_python
for %%P in (py python python3) do (
    %%P --version >nul 2>&1 && set "PY=%%P" && exit /b 0
)
exit /b 1

:fail_python
echo ERROR: Python was not found on your PATH.
echo Install Python 3.10+ from https://www.python.org/downloads/
echo Be sure to tick "Add Python to PATH" during installation.

:end_fail
echo.
pause
exit /b 1
