"""
First-run setup helper for InternIQ.
Run this once before starting the app on a new machine:
    python backend/startup.py

What it does:
  1. Verifies Python version (3.10+)
  2. Installs backend dependencies
  3. Checks for git (needed for GitHub repo sync)
  4. Creates a .env file from .env.example if one doesn't exist
  5. Runs an initial DB migration (creates tables)
  6. Prints next steps
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"


def check(msg: str):
    print(f"  ✓  {msg}")


def warn(msg: str):
    print(f"  ⚠  {msg}")


def error(msg: str):
    print(f"  ✗  {msg}")
    sys.exit(1)


def section(title: str):
    print(f"\n── {title} {'─' * max(0, 50 - len(title))}")


def main():
    print("=" * 56)
    print("  InternIQ — First-Run Setup")
    print("=" * 56)

    # ── 1. Python version ─────────────────────────────────────────────────────
    section("Python")
    major, minor = sys.version_info[:2]
    if major < 3 or minor < 10:
        error(f"Python 3.10+ required. You have {major}.{minor}")
    check(f"Python {major}.{minor}")

    # ── 2. pip install ────────────────────────────────────────────────────────
    section("Dependencies")
    print(f"  Installing from {REQUIREMENTS.name}…")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS), "--quiet"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        warn("pip install had issues:")
        print(result.stderr[:800])
    else:
        check("All Python dependencies installed")

    # ── 3. git ────────────────────────────────────────────────────────────────
    section("Git (for GitHub repo sync)")
    if shutil.which("git"):
        check("git found in PATH")
    else:
        warn("git not found — GitHub sync will be skipped at runtime")
        warn("Install git from https://git-scm.com/download/win")

    # ── 4. .env file ──────────────────────────────────────────────────────────
    section("Environment")
    if ENV_FILE.exists():
        check(f".env already exists at {ENV_FILE}")
    elif ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        check(f"Created .env from .env.example")
        warn("Open .env and add your JSEARCH_API_KEY if you have one (optional)")
    else:
        warn(".env.example not found — skipping .env creation")

    # ── 5. Create DB tables ───────────────────────────────────────────────────
    section("Database")
    try:
        # Import triggers table creation via SQLAlchemy metadata
        sys.path.insert(0, str(ROOT))
        from backend.models.database import engine, Base
        from backend.models import models  # noqa: F401 — registers all ORM models
        Base.metadata.create_all(bind=engine)
        check("Database tables created (interniq.db)")
    except Exception as exc:
        warn(f"Could not initialize database: {exc}")

    # ── 6. Next steps ─────────────────────────────────────────────────────────
    section("Done!")
    print("""
  To launch InternIQ:

    Windows:  double-click  start-desktop.bat
    Terminal: cd frontend && npm run electron:dev

  To build a distributable .exe:

    Windows:  double-click  build-app.bat
""")


if __name__ == "__main__":
    main()
