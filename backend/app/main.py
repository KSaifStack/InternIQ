"""
PyInstaller entry point for the InternIQ backend.
This file is referenced by interniq_backend.spec as the Analysis entry point.

When bundled:
  - Sets the platform-appropriate database path
  - Fixes Windows multiprocessing freeze_support
  - Starts uvicorn directly (not via module string, which breaks in bundles)
"""
import os
import sys
import multiprocessing

# Windows: required for PyInstaller + multiprocessing
if sys.platform == 'win32':
    multiprocessing.freeze_support()

# Ensure the bundle's _MEIPASS directory is on sys.path
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, bundle_dir)

# Config must be imported first — it loads .env and sets DATABASE_URL env var
from backend.config import Config, get_user_data_dir

# Log where the database will live (helpful for support)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interniq")
logger.info("[Backend] Data directory: %s", get_user_data_dir())
logger.info("[Backend] Database: %s", Config.DATABASE_URL)
logger.info("[Backend] Port: %s", Config.PORT)

# Import the FastAPI app (triggers all router imports)
from backend.main import app  # noqa: F401

import uvicorn

if __name__ == '__main__':
    uvicorn.run(
        app,
        host='127.0.0.1',
        port=Config.PORT,
        log_level='info',
        loop='asyncio',   # Force asyncio — avoids uvloop which requires Rust
        reload=False,
    )
