"""
JSearch API integration — free tier (200 requests/month).
Get your key at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""
import httpx
import logging
from datetime import datetime
from typing import List
from backend.services.github_sync import clean_description

logger = logging.getLogger(__name__)

BASE_URL = "https://jsearch.p.rapidapi.com"

_requests_used = 0
MONTHLY_LIMIT = 200


def get_requests_used() -> int:
    return _requests_used


async def search_internships(api_key: str, query: str = "software engineer intern 2026") -> List[dict]:
    global _requests_used
    if _requests_used >= MONTHLY_LIMIT:
        logger.warning("JSearch monthly quota exhausted (%d/%d)", _requests_used, MONTHLY_LIMIT)
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "date_posted": "week",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BASE_URL}/search", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("JSearch request failed: %s", e)
        return []

    _requests_used += 1
    logger.info("JSearch request %d/%d used", _requests_used, MONTHLY_LIMIT)

    jobs = []
    for job in data.get("data", []):
        title = job.get("job_title", "") or ""
        description = job.get("job_description", "") or ""
        text = f"{title} {description}".lower()

        # Only include internship roles
        if "intern" not in text and "internship" not in text:
            continue

        is_2026 = "2026" in text or "class of 2026" in text

        jobs.append({
            "company": job.get("employer_name") or "Unknown",
            "title": title or "Software Engineer Intern",
            "location": job.get("job_city") or job.get("job_country") or "Unknown",
            "state": job.get("job_state") or "",
            "is_remote": bool(job.get("job_is_remote")),
            "description": clean_description(description)[:2000],
            "application_url": job.get("job_apply_link") or "",
            "salary_min": job.get("job_min_salary"),
            "salary_max": job.get("job_max_salary"),
            "source": "jsearch",
            "posted_at": _parse_date(job.get("job_posted_at_datetime_utc")),
            "is_2026": is_2026,
        })

    logger.info("JSearch returned %d internship jobs", len(jobs))
    return jobs


def _parse_date(date_str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
    except Exception:
        return None
