@echo off
title InternIQ - Build Backend
echo ================================================
echo  InternIQ Backend Builder (PyInstaller)
echo ================================================
echo.

cd /d "%~dp0.."

echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is on your PATH.
    pause
    exit /b 1
)

echo [2/3] Installing backend dependencies...
pip install -r backend\requirements.txt --quiet
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may have failed. Continuing...
)

echo [3/3] Building backend executable with PyInstaller...
echo This may take 3-5 minutes on first run...
echo.

pyinstaller backend\interniq_backend.spec --distpath backend\dist --workpath backend\build_tmp --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  Backend built successfully!
echo  Output: backend\dist\interniq-backend\
echo ================================================
echo.
pause
