"""
Closed listing detector — visits each job's application_url and marks is_closed when confident.
Uses a thread pool for efficiency; only marks closed when page signals are clear (404, closed phrases).
Ambiguous or timeouts are left as-is.
"""
import logging
import re
import concurrent.futures
from typing import Dict, List, Tuple

import requests
from sqlalchemy.orm import Session

from backend.models.models import JobListing

logger = logging.getLogger(__name__)

# Phrases that indicate the position is closed (case-insensitive)
CLOSED_PHRASES = [
    "no longer accepting",
    "position filled",
    "job closed",
    "application period has ended",
    "this role has been filled",
    "position has been filled",
    "role has been filled",
    "we are no longer accepting",
    "applications are closed",
    "this position is closed",
    "no longer hiring",
    "opportunity has closed",
    "the page you are looking for doesn't exist",
    "the page you are looking for does not exist",
    "page not found",
    "job listing not found",
    "this position is no longer available",
    "this job listing is no longer active",
    "we couldn't find that page",
    "sorry, this job is no longer available",
    "no longer available",
    "search for jobs",
    # New phrases from user
    "this position has been filled",
    "this role is no longer available",
    "this job is no longer available",
    "this posting has expired",
    "this requisition is no longer active",
    "job requisition no longer exists",
    "position is closed",
    "opening is no longer available",
    "this opportunity is no longer available",
    "no longer accepting applications",
    "application deadline has passed",
    "we have filled this position",
    "page has moved",
    "this page no longer exists",
    "could not find the job",
    "job could not be found",
    "job has expired",
    "expired job",
    "listing has expired",
    "job listing has been removed",
    "this job has been removed",
    "been removed from our site",
    "join our talent community",
    "sign up for job alerts",
    "create a job alert",
    "no positions match",
    "0 jobs found",
    "no jobs found",
    "no results found",
    "this job is no longer available",
    "position has been filled",
    "requisition is closed",
    "job posting has expired",
    "no longer accepting applications",
]

GENERIC_LANDING_PATHS = {
    "", "/", "/careers", "/careers/", "/jobs", "/jobs/",
    "/openings", "/positions", "/work-with-us", "/join-us",
    "/join", "/about", "/home", "/error", "/404", "/search",
}

ERROR_DOMAINS = [
    "community.workday.com",
    "joinbytedance.com/search",  # ByteDance closed job redirect
]

GENERIC_PATH_KEYWORDS = [
    "/errorpage", "/maintenance", "/error", "?error=true",
    "/ctccampusboard?error",
]

# JS Rendered Domains - skip phrase matching, rely on status + redirect
JS_RENDERED_DOMAINS = [
    "wellsfargo.com",
    "mywellsfargojobs.com",
    "bankofamerica.com",
    "careers.bankofamerica.com",
    "lifeattiktok.com",
    "careers.google.com",
    "amazon.jobs",
]

# ATS-specific closed job detection
ATS_CLOSED_PATTERNS = {
    # Greenhouse: closed jobs redirect to /jobs with no ID
    "greenhouse.io": lambda url, body: "job board" in body.lower() and "/jobs/" not in url,
    
    # Lever: closed jobs show a specific message
    "jobs.lever.co": lambda url, body: "this job posting" in body.lower() or "no longer accepting" in body.lower(),
    
    # Workday: closed jobs show generic search page
    "myworkdayjobs.com": lambda url, body: "no jobs found" in body.lower() or "0 result" in body.lower(),
    
    # iCIMS: closed jobs redirect to search
    "icims.com": lambda url, body: "search for jobs" in body.lower() and "apply" not in body.lower(),
    
    # Taleo: closed jobs show error
    "taleo.net": lambda url, body: "requisition is no longer" in body.lower(),
    
    # Ashby: closed jobs return 404 JSON
    "ashbyhq.com": lambda url, body: '"error"' in body or "not found" in body.lower(),
    
    # Smart Recruiters
    "smartrecruiters.com": lambda url, body: "job is no longer available" in body.lower(),
    
    # BambooHR
    "bamboohr.com": lambda url, body: "position has been filled" in body.lower() or "no longer accepting" in body.lower(),
}

from requests.adapters import HTTPAdapter

# Shared session with robust connection pooling
SESSION = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=100)
SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})

# Use (connect, read) timeout tuple for precise enforcement
REQUEST_TIMEOUT = (3, 5) # 3s connect, 5s read
MAX_WORKERS = 50 # Increased parallelism

def is_redirect_to_homepage(original_url: str, final_url: str) -> bool:
    from urllib.parse import urlparse
    orig = urlparse(original_url)
    final = urlparse(final_url)

    orig_domain = orig.netloc.lower().replace("www.", "")
    final_domain = final.netloc.lower().replace("www.", "")
    final_path = final.path.rstrip("/").lower()
    final_full = final_url.lower()

    # Known error/maintenance domains always = closed
    if any(d in final_full for d in ERROR_DOMAINS):
        return True

    # Known generic path keywords in final URL = closed
    if any(kw in final_full for kw in GENERIC_PATH_KEYWORDS):
        return True

    # Same domain family (www normalization, http→https, subdomain change)
    if orig_domain == final_domain or orig_domain.endswith("." + final_domain) or final_domain.endswith("." + orig_domain):
        # Only closed if final path is a known generic landing with no job ID
        if final_path in GENERIC_LANDING_PATHS:
            return True
        # Final path has content — open job, possibly a clean URL redirect
        return False

    # Different domain after redirect
    final_segments = [s for s in final.path.split("/") if s]
    
    # Has a real path with 2+ segments = company rebranded, job still exists
    if len(final_segments) >= 2:
        return False

    # Different domain, no meaningful path = closed (redirected to homepage)
    return True


def is_url_closed(url: str, timeout: Tuple[int, int] = (3, 5)) -> bool | None:
    """
    Check if a job application URL is confidently closed.
    Uses HEAD requests first; falls back to GET. Detects soft-404s and redirects.
    """
    if not (url and url.strip().startswith(("http://", "https://"))):
        return True

    try:
        # 1. Try HEAD request first (much faster, no body download)
        response = SESSION.head(url, allow_redirects=True, timeout=timeout)
        
        final_url = response.url
        
        # If HEAD says 404/410/403, it's definitively closed
        if response.status_code in [404, 410, 403]:
            logger.info("Closed via HTTP status: %s -> %s", url, response.status_code)
            return True
            
        # Check redirect
        if is_redirect_to_homepage(url, final_url):
            logger.info("Soft-404 detected via redirect: %s -> %s", url, final_url)
            return True

        # If HEAD fails or non-200, we might need a GET or it's just broken
        # But for JS rendered, we stop here
        is_js_rendered = any(d in url for d in JS_RENDERED_DOMAINS)
        if response.status_code != 200:
             # Fallback to GET for non-200 HEAD (some servers don't like HEAD)
            response = SESSION.get(url, allow_redirects=True, timeout=timeout)
            final_url = response.url

        if is_js_rendered:
            # For JS sites, we already checked status and redirect
            return False

    except requests.RequestException as e:
        logger.debug("Check failed for URL %s: %s", url, e)
        return None # Ambiguous on timeout/error -> insert anyway

    if response.status_code in [404, 410, 403]:
        return True

    if response.status_code != 200:
        return None
        
    # Re-check redirect after GET if needed
    if is_redirect_to_homepage(url, final_url):
        return True

    # 3. Check body for soft-404 phrases (skip for JS rendered domains)
    if hasattr(response, 'text') and response.text:
        text = response.text.lower()
        
        # ATS-specific checks
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        host = parsed_url.netloc.lower()
        for ats_name, check_func in ATS_CLOSED_PATTERNS.items():
            if ats_name in host:
                try:
                    if check_func(url, text):
                        logger.info("ATS closed pattern match: %s (%s)", url, ats_name)
                        return True
                except Exception as e:
                    logger.debug("ATS check failed for %s: %s", url, e)

        for phrase in CLOSED_PHRASES:
            if phrase.lower() in text:
                logger.info("Closed phrase match: %s in %s", phrase, url)
                return True

    return False


def _check_one_listing(job_id: int, application_url: str) -> Tuple[int, str]:
    """
    Check a single listing's URL. Returns (job_id, "closed" | "open" | "ambiguous").
    """
    res = is_url_closed(application_url, timeout=REQUEST_TIMEOUT)
    if res is True:
        return (job_id, "closed")
    if res is False:
        return (job_id, "open")
    return (job_id, "ambiguous")


def check_and_mark_closed_listings(
    db: Session,
    limit: int = 500,
    only_open: bool = True,
) -> Dict:
    """
    For each job listing (optionally only those with is_closed=False), visit application_url
    and set is_closed=True when the page clearly indicates the job is closed.
    Uses a thread pool; ambiguous or errors leave the listing unchanged.

    Args:
        db: SQLAlchemy session
        limit: max number of listings to check this run
        only_open: if True, only check rows where is_closed is False/None

    Returns:
        {"checked": N, "closed": N, "kept": N, "ambiguous": N, "errors": [...]}
    """
    query = db.query(JobListing).filter(JobListing.application_url.isnot(None))
    if only_open:
        query = query.filter(
            (JobListing.is_closed == False) | (JobListing.is_closed.is_(None))
        )
    rows = query.limit(limit).all()

    if not rows:
        return {"checked": 0, "closed": 0, "kept": 0, "ambiguous": 0, "errors": []}

    id_to_row = {r.id: r for r in rows}
    results = []
    errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_id = {
            executor.submit(_check_one_listing, r.id, r.application_url): r.id
            for r in rows
        }
        for future in concurrent.futures.as_completed(future_to_id):
            try:
                job_id, status = future.result()
                results.append((job_id, status))
            except Exception as e:
                errors.append(str(e))

    closed_ids = [job_id for job_id, status in results if status == "closed"]
    kept = [job_id for job_id, status in results if status == "open"]
    ambiguous = [job_id for job_id, status in results if status == "ambiguous"]

    for job_id in closed_ids:
        row = id_to_row.get(job_id)
        if row:
            row.is_closed = True
            logger.info("Marked closed: job_id=%s title=%s url=%s", job_id, row.title, (row.application_url or "")[:80])

    if closed_ids:
        db.commit()

    logger.info(
        "Closed check complete: checked=%s closed=%s kept=%s ambiguous=%s",
        len(results), len(closed_ids), len(kept), len(ambiguous),
    )
    return {
        "checked": len(results),
        "closed": len(closed_ids),
        "kept": len(kept),
        "ambiguous": len(ambiguous),
        "errors": errors[:20],
    }
