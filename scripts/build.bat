@echo off
echo ===================================
echo    InternIQ Desktop - Build
echo ===================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
call npm install
if errorlevel 1 goto error

echo.
echo [2/3] Building frontend...
call npm run build
if errorlevel 1 goto error

echo.
echo [3/3] Building Electron app for Windows...
call npx electron-builder --win
if errorlevel 1 goto error

echo.
echo ===================================
echo    Build Complete!
echo ===================================
echo.
echo Installer located at:
echo   release\InternIQ Setup 1.0.0.exe
echo.
echo Portable app located at:
echo   release\InternIQ 1.0.0.exe
echo.
pause
goto end

:error
echo.
echo ===================================
echo    BUILD FAILED!
echo ===================================
echo.
pause

:end
