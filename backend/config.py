"""
Centralized configuration — reads from environment variables.
In development, values are loaded from a .env file (if present) via python-dotenv.
In production (PyInstaller bundle), set env vars in the launch environment or use
the platform-specific user data directory for the database.
"""
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Load .env if it exists (dev convenience) ──────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
        logger.info("[Config] Loaded environment from %s", _env_path)
    else:
        load_dotenv()
except ImportError:
    logger.debug("[Config] python-dotenv not installed; using system environment only")


# ── Cross-platform user data directory ────────────────────────────────────────

def get_user_data_dir() -> Path:
    """
    Returns the platform-appropriate user data directory for InternIQ.
    - Bundled (PyInstaller): uses OS app data folder so DB survives app updates
    - Development: uses the project root /data folder
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        if sys.platform == 'win32':
            base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif sys.platform == 'darwin':
            base = Path.home() / 'Library' / 'Application Support'
        else:
            base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
        data_dir = base / 'InternIQ' / 'data'
    else:
        # Development — keep data next to project root
        data_dir = Path(__file__).resolve().parent.parent / 'data'

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ── Settings ───────────────────────────────────────────────────────────────────

class Config:
    # JSearch (RapidAPI) — optional; GitHub + RemoteOK work without it
    JSEARCH_API_KEY: str = os.getenv("JSEARCH_API_KEY", "")

    # App environment
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Server port (Electron overrides this dynamically in production)
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database path — prefer explicit env var, then platform data dir
    _db_env = os.getenv("DATABASE_URL", "")
    if _db_env:
        DATABASE_URL: str = _db_env
    else:
        # Use the platform data dir for a SQLite DB
        _db_path = get_user_data_dir() / "interniq.db"
        DATABASE_URL: str = f"sqlite:///{_db_path}"
        # Also export as env var so SQLAlchemy database.py picks it up
        os.environ["DATABASE_URL"] = DATABASE_URL

    @classmethod
    def is_production(cls) -> bool:
        return cls.APP_ENV == "production"

    @classmethod
    def summary(cls) -> dict:
        return {
            "app_env": cls.APP_ENV,
            "port": cls.PORT,
            "jsearch_configured": bool(cls.JSEARCH_API_KEY),
            "database_url": cls.DATABASE_URL.split("///")[-1],
        }
