"""
Career Page Detector — Step 2
Given a company name/website, detects where they post jobs and which ATS they use.
Stores career_url and ats_provider on Company so we do not re-discover on subsequent runs.
ATS supported: Greenhouse, Lever, Workday, iCIMS, Taleo, SmartRecruiters, Ashby, BambooHR, Jobvite.
"""
import re
import requests
from typing import Optional, Tuple, List, Dict
from urllib.parse import urljoin, urlparse
from sqlalchemy.orm import Session
from datetime import datetime, timezone


# Common career page path patterns to probe
CAREER_PATHS = [
    "/careers",
    "/careers/",
    "/jobs",
    "/jobs/",
    "/work-with-us",
    "/join-us",
    "/join",
    "/about/careers",
    "/company/careers",
    "/en/careers",
    "/teams",
    "/hiring",
    "/openings",
    "/career",
]

# ATS URL signatures
ATS_URL_PATTERNS = {
    "Greenhouse": [
        r"boards\.greenhouse\.io",
        r"job-boards\.greenhouse\.io",
        r"greenhouse\.io",
    ],
    "Lever": [
        r"jobs\.lever\.co",
        r"lever\.co",
    ],
    "Workday": [
        r"myworkdayjobs\.com",
        r"workday\.com",
        r"\.wd\d+\.myworkdayjobs",
    ],
    "iCIMS": [
        r"icims\.com",
        r"jobs-.*\.icims\.com",
    ],
    "Taleo": [
        r"taleo\.net",
        r"oracle\.com/taleo",
    ],
    "SmartRecruiters": [
        r"smartrecruiters\.com",
        r"jobs\.smartrecruiters\.com",
    ],
    "Ashby": [
        r"ashbyhq\.com",
        r"jobs\.ashbyhq\.com",
    ],
    "BambooHR": [
        r"bamboohr\.com",
    ],
    "Jobvite": [
        r"jobvite\.com",
        r"jobs\.jobvite\.com",
    ],
}

# ATS HTML content signatures
ATS_HTML_PATTERNS = {
    "Greenhouse": [
        r"greenhouse\.io",
        r"data-greenhouse",
        r"gh_jid",
        r"boards\.greenhouse",
    ],
    "Lever": [
        r"lever\.co",
        r"data-lever",
        r"lever-jobs-container",
    ],
    "Workday": [
        r"workday\.com",
        r"myworkdayjobs",
        r"WD_JOB_ID",
    ],
    "iCIMS": [
        r"icims\.com",
        r"iCIMS_",
    ],
    "Taleo": [
        r"taleo\.net",
        r"taleologin",
    ],
    "SmartRecruiters": [
        r"smartrecruiters\.com",
        r"smrtr\.io",
    ],
    "Ashby": [
        r"ashbyhq\.com",
        r"ashby-job-board",
    ],
}

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def detect_ats_from_url(url: str) -> Optional[str]:
    """Detect ATS provider from URL patterns."""
    url_lower = url.lower()
    for ats_name, patterns in ATS_URL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return ats_name
    return None


def detect_ats_from_html(html: str) -> Optional[str]:
    """Detect ATS provider from HTML content patterns."""
    html_lower = html.lower()
    for ats_name, patterns in ATS_HTML_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, html_lower))
        if matches >= 1:
            return ats_name
    return None


def probe_career_page(base_url: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Probe a company's website for career pages.
    Returns (career_url, ats_provider) or None if not found.
    """
    # Normalize base URL
    parsed = urlparse(base_url)
    if not parsed.scheme:
        base_url = f"https://{base_url}"
    if not base_url.endswith("/"):
        base_url_with_slash = base_url + "/"
    else:
        base_url_with_slash = base_url

    # First check if the base URL itself is a career page
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10, allow_redirects=True)
        if response.ok:
            ats = detect_ats_from_url(response.url)
            if not ats:
                ats = detect_ats_from_html(response.text)

            # Check if page content looks like a careers page
            text_lower = response.text.lower()
            if any(kw in text_lower for kw in ["career", "job opening", "open position", "join our team", "work with us"]):
                if ats:
                    return response.url, ats
    except Exception:
        pass

    # Probe common career paths
    for path in CAREER_PATHS:
        try:
            career_url = urljoin(base_url_with_slash, path.lstrip("/"))
            response = requests.get(career_url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.ok and response.status_code == 200:
                # Check if this actually redirected to a career page
                final_url = response.url
                ats = detect_ats_from_url(final_url)
                if not ats:
                    ats = detect_ats_from_html(response.text)

                # Verify content looks career-related
                text_lower = response.text.lower()
                career_keywords = ["career", "job", "position", "opening", "role", "intern", "apply"]
                if sum(1 for kw in career_keywords if kw in text_lower) >= 2:
                    return final_url, ats
        except Exception:
            continue

    return None


def detect_career_page_for_company(
    db: Session,
    company_id: int,
    force_redetect: bool = False,
) -> Optional[Dict]:
    """
    Detect the career page for a specific company.
    Updates the company record in the database.
    """
    from backend.models.models import Company

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None

    # Skip if already detected (unless forced)
    if company.career_url and not force_redetect:
        return {
            "company": company.name,
            "career_url": company.career_url,
            "ats_provider": company.ats_provider,
            "status": "cached",
        }

    # Try to detect
    base_url = company.website_url or company.career_url
    if not base_url:
        return {
            "company": company.name,
            "career_url": None,
            "ats_provider": None,
            "status": "no_website",
        }

    result = probe_career_page(base_url)
    now = datetime.now(timezone.utc)

    if result:
        career_url, ats_provider = result
        company.career_url = career_url
        if ats_provider:
            company.ats_provider = ats_provider
        company.last_checked = now
        db.commit()

        return {
            "company": company.name,
            "career_url": career_url,
            "ats_provider": ats_provider,
            "status": "detected",
        }
    else:
        company.last_checked = now
        db.commit()

        return {
            "company": company.name,
            "career_url": None,
            "ats_provider": None,
            "status": "not_found",
        }


def detect_all_career_pages(
    db: Session,
    only_missing: bool = True,
    limit: int = 100,
) -> Dict:
    """
    Detect career pages for all companies (or only those missing career URLs).
    Returns summary stats.
    """
    from backend.models.models import Company

    query = db.query(Company)
    if only_missing:
        query = query.filter(
            (Company.career_url == None) | (Company.career_url == "")
        )

    companies = query.limit(limit).all()

    stats = {"total": len(companies), "detected": 0, "not_found": 0, "errors": []}

    for company in companies:
        try:
            result = detect_career_page_for_company(db, company.id, force_redetect=not only_missing)
            if result and result["status"] == "detected":
                stats["detected"] += 1
            elif result and result["status"] == "not_found":
                stats["not_found"] += 1
        except Exception as e:
            stats["errors"].append(f"{company.name}: {str(e)}")

    return stats
