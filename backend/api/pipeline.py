"""
Pipeline API — simplified to a single health/status endpoint.
All pipeline logic has been replaced by the scheduler.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import database, models

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/status")
def pipeline_status(db: Session = Depends(database.get_db)):
    """High-level counts for frontend status bar."""
    total = db.query(models.JobListing).filter(models.JobListing.is_active == True).count()
    jobs_2026 = db.query(models.JobListing).filter(
        models.JobListing.is_active == True,
        models.JobListing.is_2026 == True,
    ).count()
    from ..scheduler import get_last_sync
    return {
        "active_jobs": total,
        "jobs_2026": jobs_2026,
        "last_sync": get_last_sync(),
    }
