# InternIQ 

InternIQ is a desktop application that aggregates 1,700+ active software engineering internships from multiple sources. 

## Quick Start (Development)

```bash
# Clone the repo
git clone https://github.com/KareemSaif/interniq.git
cd interniq

# Set up Python backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py

# In another terminal, start frontend
cd frontend
npm install
npm run electron:dev
```

## Building the Installer

```bash
# Build complete Windows installer
.\build-app.bat
```

## Tech Stack
| Layer | Technologies |
| --- | --- |
| Frontend | React, Electron, Vite |
| Backend | FastAPI, Python, SQLite |
| Data Sources | GitHub (ZIP download), RemoteOK API |
| Distribution | PyInstaller, electron-builder |