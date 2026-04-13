"""
Background scheduler — syncs all sources every 6 hours and cleans old jobs daily.
Uses APScheduler (BackgroundScheduler).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")
_last_sync: datetime | None = None


def _get_db():
    from backend.models.database import SessionLocal
    return SessionLocal()


def run_full_sync():
    """Pull all 2026 job sources and persist to DB."""
    global _last_sync
    logger.info("[Scheduler] Starting full sync at %s", datetime.utcnow().isoformat())

    from backend.services.github_sync import sync_all_repos
    from backend.services.deduplication import JobDeduplicator
    from backend.models import models

    db = _get_db()
    dedup = JobDeduplicator()
    total_added = 0

    try:
        # ── 1. GitHub (always available, highest priority) ──────────────────
        github_jobs = sync_all_repos()
        added = _persist_jobs(db, github_jobs, dedup)
        logger.info("[Scheduler] GitHub: +%d new jobs", added)
        total_added += added

        # ── 2. RemoteOK (free, no quota) ────────────────────────────────────
        import asyncio
        from backend.services.remoteok_service import fetch_remote_internships
        remoteok_jobs = asyncio.run(fetch_remote_internships())
        added = _persist_jobs(db, remoteok_jobs, dedup)
        logger.info("[Scheduler] RemoteOK: +%d new jobs", added)
        total_added += added

        # ── 3. JSearch (respect monthly quota) ──────────────────────────────
        jsearch_key = os.environ.get("JSEARCH_API_KEY", "")
        if jsearch_key:
            from backend.services.jsearch_service import search_internships, get_requests_used, MONTHLY_LIMIT
            if get_requests_used() < MONTHLY_LIMIT:
                from backend.services.jsearch_service import search_internships
                jsearch_jobs = asyncio.run(search_internships(jsearch_key))
                added = _persist_jobs(db, jsearch_jobs, dedup)
                logger.info("[Scheduler] JSearch: +%d new jobs", added)
                total_added += added
            else:
                logger.warning("[Scheduler] JSearch: quota exhausted, skipping")
        else:
            logger.info("[Scheduler] JSearch: no API key configured, skipping")

        _last_sync = datetime.now(tz=timezone.utc)

        # Log this sync
        log = models.SyncLog(source="full_sync", jobs_added=total_added)
        db.add(log)
        db.commit()

        logger.info("[Scheduler] Sync complete — %d total new jobs", total_added)

    except Exception as e:
        logger.exception("[Scheduler] Sync failed: %s", e)
        db.rollback()
    finally:
        db.close()


def cleanup_old_jobs():
    """Mark jobs older than 60 days as inactive."""
    db = _get_db()
    try:
        from backend.models.models import JobListing
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=60)
        updated = (
            db.query(JobListing)
            .filter(JobListing.posted_at < cutoff, JobListing.is_active == True)
            .update({"is_active": False})
        )
        db.commit()
        logger.info("[Scheduler] Cleanup: marked %d old jobs inactive", updated)
    except Exception as e:
        logger.exception("[Scheduler] Cleanup failed: %s", e)
        db.rollback()
    finally:
        db.close()


def _persist_jobs(db, jobs: list, dedup: "JobDeduplicator") -> int:
    """Save new (non-duplicate) jobs to the database. Returns count of insertions."""
    from backend.models.models import Company, JobListing
    added = 0
    for job in jobs:
        company_name = (job.get("company") or "Unknown").strip()
        title = (job.get("title") or "Intern").strip()

        if not dedup.is_new(company_name, title):
            continue

        # Fingerprint
        from backend.services.deduplication import make_fingerprint
        fp = make_fingerprint(company_name, title)

        # Skip if already in DB
        exists = db.query(JobListing).filter(JobListing.listing_hash == fp).first()
        if exists:
            continue

        # Get or create company
        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()

        listing = JobListing(
            title=title,
            company_id=company.id,
            location=job.get("location"),
            state=job.get("state") or "",
            is_remote=bool(job.get("is_remote")),
            application_url=job.get("application_url") or "",
            description=job.get("description") or "",
            salary_min=job.get("salary_min"),
            salary_max=job.get("salary_max"),
            source=job.get("source") or "unknown",
            source_url=job.get("source_url") or "",
            listing_hash=fp,
            posted_at=job.get("posted_at"),
            is_2026=bool(job.get("is_2026", True)),
            is_active=True,
        )
        db.add(listing)
        added += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB commit failed: %s", e)
        return 0

    return added


def get_last_sync() -> str | None:
    return _last_sync.isoformat() if _last_sync else None


def start():
    if not scheduler.running:
        scheduler.add_job(run_full_sync, "interval", hours=6, id="full_sync", replace_existing=True)
        scheduler.add_job(cleanup_old_jobs, "interval", hours=24, id="cleanup", replace_existing=True)
        scheduler.start()
        logger.info("[Scheduler] Started — syncing every 6h, cleanup every 24h")


def stop():
    if scheduler.running:
        scheduler.shutdown(wait=False)
