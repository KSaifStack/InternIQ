import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load .env / environment config first — before any service module reads os.environ
from backend.config import Config

from backend.api import jobs, users, applications, insights, activity, pipeline, companies
from backend.api import admin
from backend.models.database import engine, Base

logger = logging.getLogger(__name__)

_startup_complete = False
_READY_FILE = Path(__file__).resolve().parent.parent / ".backend_ready"

app = FastAPI(title="InternIQ API", version="3.0.0")

_is_production = os.environ.get("APP_ENV") == "production"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _is_production else [
        "http://localhost:5173", "http://localhost:5174",
        "http://localhost:5175", "http://localhost:5176",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "InternIQ API", "version": "3.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def ready_check():
    """Returns 200 only after DB tables are created and startup sync is done."""
    if _startup_complete:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "loading"})

# Include routers
app.include_router(jobs.router)
app.include_router(users.router)
app.include_router(applications.router)
app.include_router(insights.router)
app.include_router(activity.router)
app.include_router(pipeline.router)
app.include_router(companies.router)
app.include_router(admin.router)

@app.on_event("startup")
async def on_startup():
    global _startup_complete

    try:
        _READY_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    # Create all tables fresh
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

    # Seed default user if needed
    from backend.models.database import SessionLocal
    from backend.models.models import User
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(id=1, email="user@interniq.app", full_name="InternIQ User", prefer_remote=True))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    _READY_FILE.write_text("ready")
    _startup_complete = True
    logger.info("Startup complete — wrote %s", _READY_FILE)

    # Start background scheduler (sync every 6h)
    from backend.scheduler import start as start_scheduler, run_full_sync
    start_scheduler()

    # Kick off an immediate first sync in the background
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, run_full_sync)
    logger.info("Initial sync triggered in background")


@app.on_event("shutdown")
async def on_shutdown():
    from backend.scheduler import stop as stop_scheduler
    stop_scheduler()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=not _is_production)
