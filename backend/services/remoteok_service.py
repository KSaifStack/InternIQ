"""
RemoteOK API — completely free, no key required.
Docs: https://remoteok.com/api
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import List
from backend.services.github_sync import clean_description

logger = logging.getLogger(__name__)

REMOTEOK_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "InternIQ/2.0 (job discovery platform)"}


async def fetch_remote_internships() -> List[dict]:
    """Fetch remote tech internship listings from RemoteOK."""
    try:
        async with httpx.AsyncClient(timeout=20, headers=HEADERS) as client:
            resp = await client.get(REMOTEOK_URL)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("RemoteOK fetch failed: %s", e)
        return []

    # First item is metadata/legal notice — skip it
    listings = data[1:] if isinstance(data, list) and len(data) > 1 else []

    jobs = []
    for job in listings:
        position = (job.get("position") or "").lower()
        if "intern" not in position:
            continue

        description = job.get("description") or ""
        is_2026 = "2026" in description.lower() or "2026" in position

        posted_at = None
        raw_date = job.get("date")
        if raw_date:
            try:
                posted_at = datetime.fromtimestamp(int(raw_date), tz=timezone.utc)
            except Exception:
                pass

        salary_min = _safe_int(job.get("salary_min"))
        salary_max = _safe_int(job.get("salary_max"))

        jobs.append({
            "company": job.get("company") or "Unknown",
            "title": job.get("position") or "Remote Intern",
            "location": "Remote",
            "state": "",
            "is_remote": True,
            "description": clean_description(description)[:2000],
            "application_url": job.get("url") or job.get("apply_url") or "",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "source": "remoteok",
            "posted_at": posted_at,
            "is_2026": is_2026,
        })

    logger.info("RemoteOK returned %d internship jobs", len(jobs))
    return jobs


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
