@echo off
title InternIQ Desktop
echo =====================================
echo    InternIQ Desktop - All In One
echo =====================================
echo.

REM Jump to project root (one level up from scripts/)
cd /d "%~dp0.."

REM Start the Electron desktop app (Vite + backend + Electron)
cd frontend
echo [*] Installing/updating frontend dependencies (first run may take a while)...
call npm install
echo.
echo [*] Launching InternIQ desktop (frontend + backend + Electron)...
call npm run electron:dev

echo.
echo InternIQ desktop exited. Press any key to close this window.
pause >nul

