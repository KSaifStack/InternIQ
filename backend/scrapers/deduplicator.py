"""
Deduplicator -- Step 4
Prevents duplicate job listings from appearing when scraped from multiple sources.
"""
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session


def _parse_deadline(value: Any) -> Optional[datetime]:
    """Parse deadline string to datetime for DB. Returns None if unparseable."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = (value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s[:50], fmt)
        except ValueError:
            continue
    return None


def normalize_title(title: str) -> str:
    """Normalize a job title for comparison."""
    title = title.lower().strip()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    # Remove common prefixes/suffixes
    for noise in ["intern ", "internship ", " intern", " internship", " - ", " | "]:
        title = title.replace(noise, " ")
    return title.strip()


def normalize_location(location: str) -> str:
    """Normalize a location string for comparison."""
    if not location:
        return ""
    location = location.lower().strip()
    location = re.sub(r'[^a-z0-9\s,]', '', location)
    location = re.sub(r'\s+', ' ', location)
    return location.strip()


def generate_listing_hash(company_name: str, title: str, location: str = "") -> str:
    """Generate a dedup hash from (company, title, location)."""
    norm_title = normalize_title(title)
    norm_location = normalize_location(location)
    key = f"{company_name.lower().strip()}|{norm_title}|{norm_location}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def check_duplicate(db: Session, listing_hash: str) -> Optional[int]:
    """Check if a listing with this hash already exists. Returns existing job ID or None."""
    from backend.models.models import JobListing
    existing = db.query(JobListing).filter(JobListing.listing_hash == listing_hash).first()
    return existing.id if existing else None


def deduplicate_and_insert(
    db: Session,
    company_name: str,
    job_data: Dict,
    company_id: int,
) -> Dict:
    """
    Check for duplicates before inserting. If duplicate found, merge richer data.
    Returns {"action": "inserted"|"merged"|"skipped", "job_id": int}.
    """
    from backend.models.models import JobListing

    title = job_data.get("title", "")
    location = job_data.get("location", "")
    listing_hash = generate_listing_hash(company_name, title, location)

    existing = db.query(JobListing).filter(JobListing.listing_hash == listing_hash).first()

    if existing:
        # Merge: update if new data is richer
        changed = False
        if not existing.description and job_data.get("description"):
            existing.description = job_data["description"]
            changed = True
        if not existing.required_skills and job_data.get("required_skills"):
            existing.required_skills = job_data["required_skills"]
            changed = True
        if not existing.pay_range and job_data.get("pay_range"):
            existing.pay_range = job_data["pay_range"]
            changed = True
        if not existing.tags and job_data.get("tags"):
            existing.tags = job_data["tags"]
            changed = True
        if not existing.work_mode and job_data.get("work_mode"):
            existing.work_mode = job_data["work_mode"]
            changed = True
        dl = _parse_deadline(job_data.get("deadline"))
        if not existing.deadline and dl:
            existing.deadline = dl
            changed = True

        if changed:
            db.commit()
            return {"action": "merged", "job_id": existing.id}
        return {"action": "skipped", "job_id": existing.id}

    # Insert new listing
    new_job = JobListing(
        title=title,
        description=job_data.get("description", ""),
        location=location,
        state=job_data.get("state"),
        is_remote=job_data.get("is_remote", False),
        application_url=job_data.get("application_url", ""),
        required_skills=job_data.get("required_skills"),
        company_id=company_id,
        pay_range=job_data.get("pay_range"),
        work_mode=job_data.get("work_mode"),
        deadline=_parse_deadline(job_data.get("deadline")),
        tags=job_data.get("tags"),
        listing_hash=listing_hash,
        source_url=job_data.get("source_url"),
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return {"action": "inserted", "job_id": new_job.id}
