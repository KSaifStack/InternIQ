"""
Position Verifier -- Step 3
Visits career pages, checks for intern keywords, validates freshness.
"""
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

INTERN_KEYWORDS = [
    "intern", "internship", "co-op", "coop", "new grad",
    "entry level", "entry-level", "university", "student",
    "early career", "summer", "fall intern", "spring intern",
]
FRESHNESS_KEYWORDS = ["2025", "2026", "apply now", "open", "accepting applications", "currently hiring"]
EXPIRED_KEYWORDS = ["closed", "no longer accepting", "filled", "expired", "2023", "2022"]

HIRING_SEASONS = {
    "Google": {"open_month": 8, "season": "August"},
    "Meta": {"open_month": 9, "season": "September"},
    "Apple": {"open_month": 9, "season": "September"},
    "Amazon": {"open_month": 9, "season": "September"},
    "Microsoft": {"open_month": 8, "season": "August"},
    "Netflix": {"open_month": 10, "season": "October"},
    "Goldman Sachs": {"open_month": 7, "season": "July"},
    "Morgan Stanley": {"open_month": 7, "season": "July"},
    "Jane Street": {"open_month": 6, "season": "June"},
    "Two Sigma": {"open_month": 8, "season": "August"},
    "Citadel": {"open_month": 7, "season": "July"},
    "DE Shaw": {"open_month": 7, "season": "July"},
    "NVIDIA": {"open_month": 8, "season": "August"},
    "Palantir": {"open_month": 8, "season": "August"},
    "Capital One": {"open_month": 8, "season": "August"},
    "Databricks": {"open_month": 8, "season": "August"},
    "Stripe": {"open_month": 9, "season": "September"},
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def check_for_intern_positions(html: str) -> Tuple[bool, List[str], bool]:
    """Returns (has_positions, matched_keywords, is_fresh)."""
    html_lower = html.lower()
    matched = [kw for kw in INTERN_KEYWORDS if kw in html_lower]
    has_positions = len(matched) > 0
    fresh_matches = [kw for kw in FRESHNESS_KEYWORDS if kw in html_lower]
    expired_matches = [kw for kw in EXPIRED_KEYWORDS if kw in html_lower]
    is_fresh = len(fresh_matches) > 0 and len(expired_matches) == 0
    if has_positions and not fresh_matches and not expired_matches:
        if re.search(r'202[5-9]', html, re.IGNORECASE):
            is_fresh = True
    return has_positions, matched, is_fresh


def verify_company_positions(db: Session, company_id: int) -> Dict:
    from backend.models.models import Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return {"error": "Company not found"}
    career_url = company.career_url or company.website_url
    if not career_url:
        return {"company": company.name, "has_positions": False, "status": "no_career_url"}
    now = datetime.now(timezone.utc)
    try:
        response = requests.get(career_url, headers=HEADERS, timeout=15, allow_redirects=True)
        if not response.ok:
            company.last_checked = now
            db.commit()
            return {"company": company.name, "has_positions": False, "status": f"http_{response.status_code}"}
        has_positions, matched_keywords, is_fresh = check_for_intern_positions(response.text)
        company.has_open_positions = has_positions and is_fresh
        company.last_checked = now
        if company.name in HIRING_SEASONS:
            company.hiring_season = HIRING_SEASONS[company.name]["season"]
        db.commit()
        return {"company": company.name, "has_positions": has_positions, "is_fresh": is_fresh, "matched_keywords": matched_keywords, "status": "verified"}
    except Exception as e:
        company.last_checked = now
        db.commit()
        return {"company": company.name, "has_positions": False, "status": f"error: {e}"}


def get_companies_needing_recheck(db: Session, max_age_hours: int = 24) -> List:
    from backend.models.models import Company
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)
    current_month = now.month
    companies = db.query(Company).filter((Company.career_url != None) & (Company.career_url != "")).all()
    needs_recheck = []
    for company in companies:
        should_check = False
        priority = "normal"
        if not company.last_checked:
            should_check = True
            priority = "high"
        elif company.last_checked < cutoff:
            should_check = True
            if company.name in HIRING_SEASONS:
                open_month = HIRING_SEASONS[company.name]["open_month"]
                if abs(current_month - open_month) <= 2 or abs(current_month - open_month) >= 10:
                    priority = "high"
        if should_check:
            needs_recheck.append({"company": company, "priority": priority})
    needs_recheck.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
    return needs_recheck


def verify_all_positions(db: Session, limit: int = 50, max_age_hours: int = 24) -> Dict:
    companies_to_check = get_companies_needing_recheck(db, max_age_hours)[:limit]
    stats = {"total_checked": 0, "with_positions": 0, "without_positions": 0, "errors": []}
    for item in companies_to_check:
        result = verify_company_positions(db, item["company"].id)
        stats["total_checked"] += 1
        if result.get("has_positions"):
            stats["with_positions"] += 1
        elif "error" in result.get("status", ""):
            stats["errors"].append(f"{item['company'].name}: {result['status']}")
        else:
            stats["without_positions"] += 1
    return stats


def get_seasonal_predictions(current_month: Optional[int] = None) -> List[Dict]:
    if current_month is None:
        current_month = datetime.now().month
    predictions = []
    for company_name, season in HIRING_SEASONS.items():
        months_until = (season["open_month"] - current_month) % 12
        status = "opening_now" if months_until == 0 else ("opening_soon" if months_until <= 1 else ("upcoming" if months_until <= 3 else "later"))
        predictions.append({"company": company_name, "season": season["season"], "months_until": months_until, "status": status})
    predictions.sort(key=lambda x: x["months_until"])
    return predictions
