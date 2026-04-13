"""
Jobs API — simplified 2026-only job discovery endpoints. No AI scoring.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone

from ..models import models, schemas, database

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ── Helpers ───────────────────────────────────────────────────────────────────

COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "node", "sql", "aws",
    "docker", "kubernetes", "c++", "c#", "go", "rust", "html", "css", "angular",
    "vue", "django", "flask", "spring", "mongodb", "postgresql", "redis",
    "graphql", "rest", "api", "machine learning", "ml", "ai", "data science",
    "backend", "frontend", "fullstack", "devops", "cloud", "mobile", "ios",
    "android", "flutter", "swift", "kotlin", "git", "linux", "figma",
}


def extract_skills(text: str) -> set[str]:
    text_lower = text.lower()
    return {s for s in COMMON_SKILLS if s in text_lower}


def calculate_relevance_score(job: models.JobListing, user: Optional[models.User] = None) -> int:
    """Rule-based relevance score (0-100). Replaces AI match scoring."""
    score = 50  # Base

    # Recency boost
    if job.posted_at:
        days_old = (datetime.now(tz=timezone.utc) - job.posted_at.replace(tzinfo=timezone.utc)).days
        if days_old <= 3:
            score += 20
        elif days_old <= 7:
            score += 10

    if user is None:
        return min(score, 100)

    # Skill match
    user_skills = set(s.strip().lower() for s in (user.skills or "").split(",") if s.strip())
    job_skills = extract_skills(f"{job.title} {job.description or ''} {job.required_skills or ''}")
    score += len(user_skills & job_skills) * 10

    # Remote preference
    if user.prefer_remote and job.is_remote:
        score += 15

    # Location preference
    if user.location and job.state == user.location.upper():
        score += 10

    return min(score, 100)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.JobListing])
def list_jobs(
    search: Optional[str] = Query(None),
    remote_only: bool = Query(False),
    state: Optional[str] = Query(None),
    source: Optional[str] = Query(None),         # github_simplify_interns, jsearch, remoteok …
    days_ago: Optional[int] = Query(None),        # Only jobs from last N days
    is_2026: bool = Query(True),                  # Default: only 2026 roles
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(database.get_db),
):
    """List jobs with filtering. No AI — sorted by recency."""
    query = db.query(models.JobListing).filter(models.JobListing.is_active == True)

    if is_2026:
        query = query.filter(models.JobListing.is_2026 == True)

    if search:
        for term in search.split():
            t = f"%{term}%"
            query = query.filter(
                or_(
                    models.JobListing.title.ilike(t),
                    models.JobListing.description.ilike(t),
                    models.JobListing.required_skills.ilike(t),
                )
            )

    if remote_only:
        query = query.filter(models.JobListing.is_remote == True)

    if state:
        query = query.filter(models.JobListing.state == state.upper())

    if source:
        query = query.filter(models.JobListing.source == source)

    if days_ago:
        from datetime import timedelta
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
        query = query.filter(
            or_(
                models.JobListing.posted_at >= cutoff,
                models.JobListing.posted_at.is_(None),
            )
        )

    query = query.order_by(models.JobListing.posted_at.desc().nullslast(), models.JobListing.id.desc())
    jobs = query.offset(skip).limit(limit).all()

    # Attach rule-based relevance scores (non-persisted field)
    user = db.query(models.User).filter(models.User.id == 1).first()
    for job in jobs:
        job.relevance_score = calculate_relevance_score(job, user)

    # Log search
    if search or state or remote_only:
        try:
            db.add(models.SearchLog(
                user_id=1,
                query=search or "",
                state_filter=state,
                remote_filter=remote_only,
                results_count=len(jobs),
            ))
            db.commit()
        except Exception:
            db.rollback()

    return jobs


@router.get("/states", response_model=List[str])
def get_states(db: Session = Depends(database.get_db)):
    """Return distinct US states that have active job listings."""
    rows = (
        db.query(models.JobListing.state)
        .filter(
            models.JobListing.is_active == True,
            models.JobListing.state.isnot(None),
            models.JobListing.state != "",
        )
        .distinct()
        .order_by(models.JobListing.state)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/sources", response_model=List[str])
def get_sources(db: Session = Depends(database.get_db)):
    """Return distinct data sources."""
    rows = (
        db.query(models.JobListing.source)
        .filter(models.JobListing.source.isnot(None), models.JobListing.source != "")
        .distinct()
        .order_by(models.JobListing.source)
        .all()
    )
    return [r[0] for r in rows]


@router.post("/sync")
async def manual_sync(background_tasks: BackgroundTasks):
    """Manually trigger a full sync of all sources in the background."""
    from ..scheduler import run_full_sync
    background_tasks.add_task(run_full_sync)
    return {"message": "Full sync started in background"}


@router.get("/sync-log")
def get_sync_log(limit: int = Query(50, ge=1, le=200), db: Session = Depends(database.get_db)):
    """Recent sync log entries."""
    logs = db.query(models.SyncLog).order_by(models.SyncLog.ran_at.desc()).limit(limit).all()
    return {"logs": [
        {
            "id": l.id,
            "source": l.source,
            "ran_at": l.ran_at.isoformat() if l.ran_at else None,
            "jobs_added": l.jobs_added,
            "errors": l.errors,
        }
        for l in logs
    ]}


@router.get("/{job_id}", response_model=schemas.JobListing)
def get_job(job_id: int, db: Session = Depends(database.get_db)):
    job = db.query(models.JobListing).filter(models.JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.relevance_score = calculate_relevance_score(job)
    return job


@router.post("/{job_id}/hide")
def hide_job(job_id: int, db: Session = Depends(database.get_db)):
    """Mark a job as inactive (hide from feed)."""
    job = db.query(models.JobListing).filter(models.JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    db.commit()
    return {"status": "ok", "message": "Job hidden from feed"}
