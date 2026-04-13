"""
Unified scraper runner — runs all job sources in sequence with error isolation.
If one scraper crashes, we log and continue the rest. Used by POST /api/jobs/sync-all
and by the optional 24-hour scheduler (run_scheduled_sync).
"""
import logging
import time
from typing import Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Rate Limiting Configuration
MIN_REQUEST_INTERVAL = 2.0  # Seconds to wait between scraper sources
WEBHOOK_URL = os.environ.get("INTERNIQ_WEBHOOK_URL", None) # Optional: send new jobs to a webhook

def _send_webhook(jobs_count: int):
    """Send a webhook notification if configured."""
    if not WEBHOOK_URL:
        return
    try:
        import requests
        requests.post(WEBHOOK_URL, json={"jobs_added": jobs_count}, timeout=5)
        logger.info("Webhook sent successfully")
    except Exception as e:
        logger.warning(f"Failed to send webhook: {e}")

def _rate_limit():
    """Simple sleep-based rate limiter between major scraper sources."""
    # In a production app, this would be a distributed lock or token bucket
    logger.info("Rate limiting: sleeping for %s seconds...", MIN_REQUEST_INTERVAL)
    time.sleep(MIN_REQUEST_INTERVAL)


def run_all_scrapers(db: Session) -> Dict[str, Any]:
    """
    Run all scrapers in sequence: GitHub, Greenhouse, Lever, Workday, Ashby, Rippling, iCIMS, BambooHR, Jobvite.
    Returns a summary and logs each run to SyncLog.
    """
    from backend.models.models import SyncLog
    
    summary = {
        "github": {"inserted": 0, "merged": 0, "skipped_closed": 0, "skipped_ambiguous": 0},
        "greenhouse": {"added": 0},
        "lever": {"added": 0},
        "workday": {"added": 0},
        "ashby": {"added": 0},
        "rippling": {"added": 0},
        "icims": {"added": 0},
        "bamboohr": {"added": 0},
        "jobvite": {"added": 0},
        "errors": [],
    }

    def _log_sync(source: str, added: int, checked: int = None, closed: int = None, skipped_closed: int = 0, skipped_ambiguous: int = 0, error: str = None):
        try:
            log = SyncLog(
                source=source,
                jobs_added=added,
                jobs_checked=checked,
                jobs_closed=closed,
                skipped_closed=skipped_closed,
                skipped_ambiguous=skipped_ambiguous,
                errors=error
            )
            db.add(log)
            db.commit()
        except Exception as ex:
            logger.error("Failed to write sync log for %s: %s", source, ex)
            db.rollback()

    # 1. GitHub
    try:
        from backend.scrapers.company_discovery import sync_github_internship_listings
        res = sync_github_internship_listings(db)
        summary["github"].update(res)
        _log_sync("github", res.get("inserted", 0), skipped_closed=res.get("skipped_closed", 0), skipped_ambiguous=res.get("skipped_ambiguous", 0))
    except Exception as e:
        logger.exception("GitHub sync failed")
        _log_sync("github", 0, error=str(e))
        summary["errors"].append(f"github: {e!s}")
        
    _rate_limit()

    # 2. Greenhouse
    try:
        from backend.real_seed import run_greenhouse_scraper
        res = run_greenhouse_scraper(db)
        summary["greenhouse"]["added"] = res.get("added", 0)
        _log_sync("greenhouse", res.get("added", 0))
    except Exception as e:
        _log_sync("greenhouse", 0, error=str(e))
        summary["errors"].append(f"greenhouse: {e!s}")

    _rate_limit()
    
    # 3. Lever
    try:
        from backend.real_seed import run_lever_scraper
        res = run_lever_scraper(db)
        summary["lever"]["added"] = res.get("added", 0)
        _log_sync("lever", res.get("added", 0))
    except Exception as e:
        _log_sync("lever", 0, error=str(e))
        summary["errors"].append(f"lever: {e!s}")

    _rate_limit()
    
    # 4. Workday
    try:
        from backend.scrapers.workday_scraper import run_workday_scraper
        res = run_workday_scraper(db)
        summary["workday"]["added"] = res.get("added", 0)
        _log_sync("workday", res.get("added", 0))
    except Exception as e:
        _log_sync("workday", 0, error=str(e))
        summary["errors"].append(f"workday: {e!s}")

    # 5. Ashby
    try:
        from backend.scrapers.ashby_scraper import run_ashby_scraper
        res = run_ashby_scraper(db)
        summary["ashby"]["added"] = res.get("added", 0)
        _log_sync("ashby", res.get("added", 0))
    except Exception as e:
        _log_sync("ashby", 0, error=str(e))
        summary["errors"].append(f"ashby: {e!s}")

    # 6. Rippling
    try:
        from backend.scrapers.rippling_scraper import run_rippling_scraper
        res = run_rippling_scraper(db)
        summary["rippling"]["added"] = res.get("added", 0)
        _log_sync("rippling", res.get("added", 0))
    except Exception as e:
        _log_sync("rippling", 0, error=str(e))
        summary["errors"].append(f"rippling: {e!s}")

    # 7. iCIMS
    try:
        from backend.scrapers.icims_scraper import run_icims_scraper
        res = run_icims_scraper(db)
        summary["icims"]["added"] = res.get("added", 0)
        _log_sync("icims", res.get("added", 0))
    except Exception as e:
        _log_sync("icims", 0, error=str(e))
        summary["errors"].append(f"icims: {e!s}")

    # 8. BambooHR
    try:
        from backend.scrapers.bamboohr_scraper import run_bamboohr_scraper
        res = run_bamboohr_scraper(db)
        summary["bamboohr"]["added"] = res.get("added", 0)
        _log_sync("bamboohr", res.get("added", 0))
    except Exception as e:
        _log_sync("bamboohr", 0, error=str(e))
        summary["errors"].append(f"bamboohr: {e!s}")

    # 9. Jobvite
    try:
        from backend.scrapers.jobvite_scraper import run_jobvite_scraper
        res = run_jobvite_scraper(db)
        summary["jobvite"]["added"] = res.get("added", 0)
        _log_sync("jobvite", res.get("added", 0))
    except Exception as e:
        _log_sync("jobvite", 0, error=str(e))
        summary["errors"].append(f"jobvite: {e!s}")

    # Send webhook if enabled
    total_added = sum(s.get("inserted", 0) or s.get("added", 0) for s in summary.values() if isinstance(s, dict))
    if total_added > 0:
        _send_webhook(total_added)
        
    return summary


def run_scheduled_sync(db: Session) -> Dict[str, Any]:
    """
    Run full sync (all scrapers) then closed-detection. Intended for 24-hour background
    scheduler: run_all_scrapers(db) then check_and_mark_closed_listings(db).
    """
    summary = run_all_scrapers(db)
    try:
        from backend.scrapers.closed_detector import check_and_mark_closed_listings
        closed_result = check_and_mark_closed_listings(db, limit=500, only_open=True)
        summary["closed_detector"] = closed_result
    except Exception as e:
        logger.exception("Closed detector failed: %s", e)
        summary["errors"].append(f"closed_detector: {e!s}")
    return summary
