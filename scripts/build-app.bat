@echo off
title InternIQ 2.7 - Production Build
setlocal enabledelayedexpansion
echo ============================================================
echo  InternIQ 2.7 - Production Build
echo  Builds a standalone Windows installer. No Python required
echo  on the target machine.
echo ============================================================
echo.

cd /d "%~dp0.."

REM ── Step 1: Create clean virtual environment ───────────────────────────────
echo [1/6] Creating clean build virtual environment...
if exist venv_build (
    echo   Removing old venv_build...
    rmdir /s /q venv_build
)
python -m venv venv_build
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Could not create virtual environment.
    echo  Make sure Python 3.11+ is installed and on PATH.
    pause & exit /b 1
)
echo   Created venv_build
echo.

REM ── Step 2: Upgrade pip + wheel infrastructure ─────────────────────────────
echo [2/6] Upgrading pip, setuptools, and wheel...
call venv_build\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel --quiet
if %errorlevel% neq 0 (
    echo   WARNING: pip upgrade had issues, continuing...
)
echo   Done.
echo.

REM ── Step 3: Install dependencies (pre-built wheels ONLY, no Rust) ──────────
echo [3/6] Installing backend dependencies (wheels only, no compilation)...

REM Install almost everything with --only-binary to avoid ANY native compilation
pip install --only-binary :all: ^
    "fastapi==0.115.6" ^
    "uvicorn==0.34.0" ^
    "sqlalchemy==2.0.36" ^
    "pydantic==2.10.3" ^
    "pydantic-settings==2.7.0" ^
    "python-dotenv>=1.0.0" ^
    "apscheduler>=3.10.0" ^
    "httpx==0.28.1" ^
    "httpcore>=1.0.7" ^
    "h11>=0.14.0" ^
    "requests==2.32.3" ^
    "soupsieve>=2.5" ^
    --quiet

if %errorlevel% neq 0 (
    echo   WARNING: Some packages may have failed. Retrying individually...
    pip install "fastapi" "uvicorn" "sqlalchemy" "pydantic" "python-dotenv" "apscheduler" "httpx" "requests" --quiet
)

REM beautifulsoup4 is pure Python — safe to install with source fallback
pip install beautifulsoup4 --quiet

REM Install PyInstaller itself
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: PyInstaller installation failed.
    pause & exit /b 1
)
echo   All dependencies installed.
echo.

REM ── Step 4: Build Python backend with PyInstaller ──────────────────────────
echo [4/6] Building Python backend (single-file exe)...
echo   This may take 3-5 minutes...
echo.

pyinstaller backend\interniq_prod.spec ^
    --distpath backend\dist ^
    --workpath backend\build_tmp ^
    --noconfirm ^
    --clean

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: PyInstaller build failed. Check output above.
    echo.
    echo  Common fixes:
    echo    - Run: pip install pyinstaller --upgrade
    echo    - Run: pip install --upgrade setuptools
    echo    - Delete backend\build_tmp and retry
    pause & exit /b 1
)

REM Verify the exe was produced
if not exist "backend\dist\interniq-backend.exe" (
    echo.
    echo  ERROR: Expected backend\dist\interniq-backend.exe not found.
    echo  Check the PyInstaller output above for errors.
    pause & exit /b 1
)

echo   Backend built: backend\dist\interniq-backend.exe
for %%A in (backend\dist\interniq-backend.exe) do (
    set /a SIZE=%%~zA / 1048576
    echo   Size: !SIZE! MB
)
echo.

REM ── Step 5: Build React + Electron frontend ─────────────────────────────────
echo [5/6] Building Electron frontend...
cd frontend
call npm install --silent
if %errorlevel% neq 0 (
    echo   ERROR: npm install failed.
    cd .. & pause & exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo   ERROR: Vite build failed.
    cd .. & pause & exit /b 1
)

call npm run electron:build:win
if %errorlevel% neq 0 (
    echo   ERROR: electron-builder failed.
    cd .. & pause & exit /b 1
)
cd ..
echo.

REM ── Step 6: Collect distribution files ──────────────────────────────────────
echo [6/6] Packaging distribution files...
if exist "InternIQ-2.7.0" rmdir /s /q "InternIQ-2.7.0"
mkdir "InternIQ-2.7.0"

set FOUND=0
if exist "frontend\release\InternIQ Setup 2.7.0.exe" (
    copy "frontend\release\InternIQ Setup 2.7.0.exe" "InternIQ-2.7.0\"
    set FOUND=1
)
if exist "frontend\release\InternIQ 2.7.0.exe" (
    copy "frontend\release\InternIQ 2.7.0.exe" "InternIQ-2.7.0\"
    set FOUND=1
)
REM Fallback: grab any exe in the release folder
if !FOUND!==0 (
    for %%F in (frontend\release\*.exe) do (
        copy "%%F" "InternIQ-2.7.0\"
    )
)

if exist "README.md" copy "README.md" "InternIQ-2.7.0\" >nul 2>&1

if exist "InternIQ-2.7.0.zip" del "InternIQ-2.7.0.zip"
powershell -Command "Compress-Archive -Path 'InternIQ-2.7.0\*' -DestinationPath 'InternIQ-2.7.0.zip' -Force"
echo.

echo ============================================================
echo  BUILD COMPLETE!
echo.
echo  Distribution files:
for %%F in (frontend\release\*.exe) do echo    %%F
echo.
echo  Zip archive:  InternIQ-2.7.0.zip
echo.
echo  Users need: Nothing. Just run the exe.
echo  Data saved to: %%APPDATA%%\InternIQ\data\
echo ============================================================
echo.
pause
