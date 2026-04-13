from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/activity", tags=["activity"])


class ActivityCreate(BaseModel):
    activity_type: str
    job_id: Optional[int] = None
    metadata: Optional[dict] = None


@router.post("/log")
def log_activity(activity: ActivityCreate):
    """No-op activity logger — kept for API compatibility."""
    return {"status": "logged"}
