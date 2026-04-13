@echo off
echo ===================================
echo    InternIQ Desktop - Development
echo ===================================
echo.

cd /d "%~dp0"
cd ..

echo [1/3] Starting Python Backend...
echo    Working directory: %CD%
echo.

start "InternIQ Backend" cmd /k "backend\venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Vite Frontend...
echo.
start "InternIQ Frontend" cmd /k "cd frontend && npm run dev"

echo [3/3] Starting Electron...
echo.

cd frontend
set NODE_ENV=development
npx electron electron/main.cjs

echo.
echo InternIQ has been closed.
pause
