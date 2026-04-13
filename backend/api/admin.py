"""
Admin API — health dashboard for all data sources.
"""
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from ..models import database, models
from ..scheduler import get_last_sync
from ..services.jsearch_service import get_requests_used, MONTHLY_LIMIT

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/health")
def system_health(db: Session = Depends(database.get_db)):
    """Full system health — data sources, DB stats, last sync times."""
    # ── DB stats ──────────────────────────────────────────────────────────────
    total_jobs = db.query(func.count(models.JobListing.id)).scalar() or 0
    active_jobs = db.query(func.count(models.JobListing.id)).filter(
        models.JobListing.is_active == True
    ).scalar() or 0
    jobs_2026 = db.query(func.count(models.JobListing.id)).filter(
        models.JobListing.is_2026 == True,
        models.JobListing.is_active == True,
    ).scalar() or 0

    # ── Per-source counts ─────────────────────────────────────────────────────
    source_counts = {}
    rows = (
        db.query(models.JobListing.source, func.count(models.JobListing.id))
        .filter(models.JobListing.is_active == True)
        .group_by(models.JobListing.source)
        .all()
    )
    for src, cnt in rows:
        source_counts[src or "unknown"] = cnt

    # ── Last sync log per source ───────────────────────────────────────────────
    sync_sources = [
        "github_simplify_interns", "github_speedyapply_swe",
        "github_vanshb_interns", "github_speedyapply_ai",
        "github_simplify_newgrad", "remoteok", "jsearch", "full_sync",
    ]
    sync_status = {}
    for src in sync_sources:
        latest = (
            db.query(models.SyncLog)
            .filter(models.SyncLog.source == src)
            .order_by(models.SyncLog.ran_at.desc())
            .first()
        )
        if latest:
            sync_status[src] = {
                "last_ran": latest.ran_at.isoformat() if latest.ran_at else None,
                "jobs_added": latest.jobs_added,
                "status": "error" if latest.errors else "healthy",
            }
        else:
            sync_status[src] = {"last_ran": None, "jobs_added": 0, "status": "never"}

    # ── JSearch quota ─────────────────────────────────────────────────────────
    jsearch_key_set = bool(os.environ.get("JSEARCH_API_KEY"))
    jsearch_used = get_requests_used()

    return {
        "database": {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "jobs_2026": jobs_2026,
            "jobs_by_source": source_counts,
        },
        "sources": {
            "github": {
                "repos": 5,
                "status": "active",
                "last_sync": sync_status.get("full_sync", {}).get("last_ran"),
            },
            "remoteok": {
                "status": "active",
                "cost": "free",
                "last_sync": sync_status.get("remoteok", {}).get("last_ran"),
            },
            "jsearch": {
                "status": "active" if jsearch_key_set else "no_key",
                "requests_used": jsearch_used,
                "monthly_limit": MONTHLY_LIMIT,
                "quota_ok": jsearch_used < MONTHLY_LIMIT,
                "last_sync": sync_status.get("jsearch", {}).get("last_ran"),
            },
        },
        "last_full_sync": get_last_sync(),
        "sync_log": sync_status,
    }
