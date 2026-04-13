"""
ATS API clients — Step 4
Calls Greenhouse and Lever public APIs when career_url is known, for structured job data.
"""
import json
import re
import urllib.request
from typing import List, Dict, Optional, Tuple

GREENHOUSE_BOARD_PATTERN = re.compile(
    r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
LEVER_BOARD_PATTERN = re.compile(
    r"jobs\.lever\.co/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)


def get_greenhouse_board_from_url(career_url: str) -> Optional[str]:
    """Extract Greenhouse board name from URL, e.g. boards.greenhouse.io/stripe -> stripe."""
    if not career_url:
        return None
    m = GREENHOUSE_BOARD_PATTERN.search(career_url)
    return m.group(1) if m else None


def get_lever_board_from_url(career_url: str) -> Optional[str]:
    """Extract Lever board name from URL, e.g. jobs.lever.co/notion -> notion."""
    if not career_url:
        return None
    m = LEVER_BOARD_PATTERN.search(career_url)
    return m.group(1) if m else None


def fetch_greenhouse_jobs_api(board_name: str) -> List[Dict]:
    """Fetch job list from Greenhouse public API. Returns list of {title, url, location, id}."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_name}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; InternIQ/1.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []
    jobs = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        loc = job.get("location", {})
        location = loc.get("name", "") if isinstance(loc, dict) else str(loc)
        jobs.append({
            "title": title,
            "url": job.get("absolute_url", ""),
            "location": location,
            "id": str(job.get("id", "")),
        })
    return jobs


def fetch_lever_jobs_api(board_name: str) -> List[Dict]:
    """Fetch job list from Lever public API. Returns list of {title, url, location, description}."""
    url = f"https://api.lever.co/v0/postings/{board_name}?mode=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; InternIQ/1.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []
    jobs = []
    for job in data if isinstance(data, list) else []:
        title = job.get("text", "")
        cats = job.get("categories", {}) or {}
        location = cats.get("location", "") if isinstance(cats, dict) else ""
        jobs.append({
            "title": title,
            "url": job.get("hostedUrl", "") or job.get("applyUrl", ""),
            "location": location,
            "description": (job.get("descriptionPlain") or "")[:2000],
        })
    return jobs


def get_jobs_via_ats_api(career_url: str) -> Tuple[Optional[str], List[Dict]]:
    """
    If career_url is Greenhouse or Lever, fetch jobs via public API.
    Returns (ats_provider, list of job dicts) or (None, []) if not supported or failed.
    """
    board = get_greenhouse_board_from_url(career_url)
    if board:
        return "Greenhouse", fetch_greenhouse_jobs_api(board)
    board = get_lever_board_from_url(career_url)
    if board:
        return "Lever", fetch_lever_jobs_api(board)
    return None, []
