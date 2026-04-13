# InternIQ Desktop App

This is the Electron desktop version of InternIQ - a job board for internship listings.

## Features

- All-in-one desktop application
- Runs Python backend automatically
- SQLite database stored locally
- No browser required
- Works offline

## Development

### Prerequisites

- Node.js 18+
- Python 3.10+
- Backend virtual environment set up

### Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development mode (starts both backend and Electron):
```bash
# On Windows:
npm run electron:dev

# Or manually:
# Terminal 1: Start Python backend
cd ..\backend
venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Electron
cd frontend
npm run electron:win
```

### Development Scripts

- `npm run dev` - Start Vite dev server only
- `npm run electron:dev` - Start both backend and Electron
- `npm run electron:win` - Start Electron only (Windows)
- `npm run electron` - Start Electron only (Mac/Linux)

## Building for Production

### Windows
```bash
npm run electron:build:win
```
Creates:
- `release/InternIQ Setup 1.0.0.exe` - Installer
- `release/InternIQ 1.0.0.exe` - Portable executable

### macOS
```bash
npm run electron:build:mac
```
Creates:
- `release/InternIQ-1.0.0.dmg` - Disk image

### Linux
```bash
npm run electron:build:linux
```
Creates:
- `release/InternIQ-1.0.0.AppImage` - Portable AppImage
- `release/interniq_1.0.0_amd64.deb` - Debian package

### Build for All Platforms
```bash
npm run dist
```

## Project Structure

```
frontend/
├── electron/
│   ├── main.js       # Electron main process
│   ├── preload.js    # Preload script for security
│   └── electron-builder.json  # Build configuration
├── src/              # React frontend code
├── dist/             # Built frontend (created by npm run build)
└── release/          # Built executables (created by electron-builder)
```

## Troubleshooting

### Python backend not starting
- Ensure your Python virtual environment is set up in `backend/venv`
- Check that all Python dependencies are installed

### White screen in production build
- Make sure you've run `npm run build` before building Electron
- Check that `dist/` folder exists and contains the built files

### Port already in use
- Make sure no other instance of the app is running
- Kill any lingering Python processes: `taskkill /f /im python.exe` (Windows) or `pkill -f "uvicorn"` (Mac/Linux)

## License

Private - Closed source
