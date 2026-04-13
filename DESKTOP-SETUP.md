# InternIQ Desktop App Setup

Your InternIQ app is now configured to run as a desktop application! Here's how to use it:

## Quick Start

### Option 1: Development Mode (Fastest)

**Windows (Easiest):**
```bash
cd frontend
start.bat
```

**Cross-platform:**
```bash
cd frontend

# Terminal 1 - Start Backend
cd ../backend
venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Start Electron
cd frontend
npm install
npm run electron:win     # Windows
npm run electron         # Mac/Linux
```

### Option 2: Build for Distribution

**Windows (One-click):**
```bash
cd frontend
build.bat
```

**Manual build:**
```bash
cd frontend
npm install
npm run electron:build:win   # Creates .exe installer
```

## What Was Created

```
frontend/
├── electron/
│   ├── main.js              # Electron entry point
│   ├── preload.js           # Secure bridge to React
│   └── electron-builder.json # Build configuration
├── start.bat                # Quick Windows dev launcher
├── build.bat                # Quick Windows build script
├── start-dev.js             # Automated dev script
├── ELECTRON.md              # Detailed documentation
└── package.json             # Updated with Electron scripts
```

## How It Works

1. **Development:**
   - Python backend runs on localhost:8000
   - Electron loads `http://localhost:5173` (Vite dev server)
   - Hot reload works for React code

2. **Production:**
   - Backend bundled with app and auto-starts
   - React built to `dist/` and served via `file://`
   - Everything runs locally, no internet needed

## Scripts Added

| Script | Description |
|--------|-------------|
| `npm run electron:dev` | Start backend + Electron (auto) |
| `npm run electron:win` | Start Electron only (Windows) |
| `npm run electron` | Start Electron only (Mac/Linux) |
| `npm run electron:build` | Build for current platform |
| `npm run electron:build:win` | Build Windows installer |
| `npm run electron:build:mac` | Build macOS .dmg |
| `npm run electron:build:linux` | Build Linux AppImage |
| `npm run dist` | Build all platforms |

## Requirements

- Node.js 18+ (with npm)
- Python backend with venv set up
- Windows/Mac/Linux

## Installation Steps

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development

**Windows:**
```bash
start.bat
```

**Mac/Linux:**
```bash
npm run electron:dev
```

### 3. Build Distribution

**Windows:**
```bash
build.bat
```

**Others:**
```bash
npm run electron:build
```

Find your installer in `frontend/release/`.

## Troubleshooting

### "Python backend not found"
- Make sure your Python venv is in `backend/venv/`
- Backend should run: `cd backend && venv\Scripts\python -m uvicorn backend.main:app --port 8000`

### "Port 8000 already in use"
- Close other instances: `taskkill /f /im python.exe` (Windows) or `pkill -f uvicorn` (Mac/Linux)
- Or the app will use the existing backend

### "White screen in Electron"
- Make sure backend is running on port 8000
- Check DevTools: `Ctrl+Shift+I` (or `Cmd+Option+I` on Mac)

### Build fails
- Make sure you've run `npm install`
- Try deleting `node_modules` and reinstalling

## Next Steps

1. **Test it:** Run `start.bat` to verify everything works
2. **Customize:** Add your own icon by creating `frontend/public/icon.ico`
3. **Build:** Run `build.bat` to create your `.exe`
4. **Distribute:** Share `release/InternIQ Setup 1.0.0.exe`

## Features

✅ Single executable - no installation needed (portable version)
✅ Auto-starts Python backend
✅ Works offline
✅ Native window controls
✅ Cross-platform (Windows, Mac, Linux)
✅ Automatic updates support (with config)

Your app is ready to go!
