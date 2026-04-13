"""
Scraping Scheduler -- Background task for periodic scraping with deduplication.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
import re


REQUEST_DELAY = 3
MAX_JOBS_PER_COMPANY = 20


class ScrapingStatus:
    is_running: bool = False
    last_run: Optional[datetime] = None
    companies_processed: int = 0
    jobs_found: int = 0
    jobs_added: int = 0
    errors: list = []
    current_company: str = ""

scraping_status = ScrapingStatus()


def extract_state_from_location(location: str) -> Optional[str]:
    if not location:
        return None
    location_upper = location.upper()
    us_states = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
        "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
        "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
        "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
        "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
        "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
        "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
        "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
        "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
        "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI", "WYOMING": "WY",
    }
    for state_name, abbr in us_states.items():
        if state_name in location_upper:
            return abbr
    match = re.search(r',\s*([A-Z]{2})\s*$', location_upper)
    if match:
        return match.group(1)
    cities = {
        "SAN FRANCISCO": "CA", "LOS ANGELES": "CA", "SAN JOSE": "CA",
        "SEATTLE": "WA", "PORTLAND": "OR", "AUSTIN": "TX", "HOUSTON": "TX",
        "DALLAS": "TX", "DENVER": "CO", "BOSTON": "MA", "NEW YORK": "NY",
        "CHICAGO": "IL", "MIAMI": "FL", "ATLANTA": "GA", "PHOENIX": "AZ",
    }
    for city, abbr in cities.items():
        if city in location_upper:
            return abbr
    return None


async def scrape_single_company(db: Session, company, use_ai: bool = True) -> int:
    from backend.scrapers.career_page_scraper import get_job_listings_from_career_page, scrape_job_detail
    from backend.scrapers.ai_job_parser import parse_job_with_ai, is_ollama_available, tag_job_listing, detect_work_mode, extract_pay_range, extract_deadline
    from backend.scrapers.deduplicator import generate_listing_hash, deduplicate_and_insert
    from backend.models.models import JobListing

    global scraping_status
    career_url = company.career_url or company.website_url
    if not career_url:
        return 0
    scraping_status.current_company = company.name
    new_jobs_count = 0

    try:
        job_listings = await get_job_listings_from_career_page(career_url)
        if not job_listings:
            return 0
        scraping_status.jobs_found += len(job_listings)

        for job_data in job_listings[:MAX_JOBS_PER_COMPANY]:
            job_url = job_data.get("url", "")
            if not job_url:
                continue

            title = job_data.get("title", "Unknown")
            location = job_data.get("location", "")
            description = job_data.get("description", "")  # Lever API provides description
            is_remote = "remote" in location.lower() if location else False
            required_skills = ""
            pay_range = None
            work_mode = detect_work_mode(location)
            deadline_str = None

            # Try AI parsing (or OpenAI/Claude/Gemini if configured in Profile)
            ai_provider = None
            ai_api_key = None
            if use_ai:
                from ..models.models import User
                user = db.query(User).filter(User.id == 1).first()
                if user and user.ai_provider and user.ai_api_key:
                    ai_provider = user.ai_provider
                    ai_api_key = user.ai_api_key

            if use_ai and (is_ollama_available() or (ai_provider and ai_api_key)):
                try:
                    job_html = await scrape_job_detail(job_url)
                    if job_html:
                        parsed = parse_job_with_ai(job_html, job_url, ai_provider, ai_api_key)
                        if parsed:
                            title = parsed.get("title") or title
                            description = parsed.get("description", "") or description
                            location = parsed.get("location") or location
                            is_remote = parsed.get("is_remote", is_remote)
                            required_skills = parsed.get("required_skills", "")
                            pay_range = parsed.get("salary") or pay_range
                            deadline_str = parsed.get("deadline")
                except Exception as e:
                    scraping_status.errors.append(f"AI parse {job_url}: {e}")
            if not deadline_str and (description or title):
                deadline_str = extract_deadline(description or title)

            state = extract_state_from_location(location)
            tags = tag_job_listing(description or title, title)

            result = deduplicate_and_insert(db, company.name, {
                "title": title,
                "description": description,
                "location": location,
                "state": state,
                "is_remote": is_remote,
                "application_url": job_url,
                "required_skills": required_skills,
                "pay_range": pay_range,
                "work_mode": work_mode,
                "deadline": deadline_str,
                "tags": tags,
                "source_url": career_url,
            }, company.id)

            if result["action"] == "inserted":
                new_jobs_count += 1
                scraping_status.jobs_added += 1

            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        scraping_status.errors.append(f"Error scraping {company.name}: {e}")
        db.rollback()

    return new_jobs_count


async def run_full_scrape(db: Session, max_companies: int = 50, use_ai: bool = True) -> Dict:
    from backend.scrapers.company_discovery import discover_companies
    from backend.scrapers.company_source import get_all_companies_from_db

    global scraping_status
    if scraping_status.is_running:
        return {"status": "already_running", "message": "Scraping is already in progress"}

    scraping_status.is_running = True
    scraping_status.last_run = datetime.now()
    scraping_status.companies_processed = 0
    scraping_status.jobs_found = 0
    scraping_status.jobs_added = 0
    scraping_status.errors = []
    scraping_status.current_company = ""

    try:
        discover_companies(db)
        companies = get_all_companies_from_db(db)[:max_companies]
        for company in companies:
            await scrape_single_company(db, company, use_ai)
            scraping_status.companies_processed += 1
            await asyncio.sleep(REQUEST_DELAY)
        return {
            "status": "completed",
            "companies_processed": scraping_status.companies_processed,
            "jobs_found": scraping_status.jobs_found,
            "jobs_added": scraping_status.jobs_added,
            "errors": scraping_status.errors[:10],
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "errors": scraping_status.errors}
    finally:
        scraping_status.is_running = False
        scraping_status.current_company = ""


def get_scraping_status() -> Dict:
    return {
        "is_running": scraping_status.is_running,
        "last_run": scraping_status.last_run.isoformat() if scraping_status.last_run else None,
        "companies_processed": scraping_status.companies_processed,
        "jobs_found": scraping_status.jobs_found,
        "jobs_added": scraping_status.jobs_added,
        "current_company": scraping_status.current_company,
        "error_count": len(scraping_status.errors),
    }


async def trigger_scrape(db: Session, max_companies: int = 50, use_ai: bool = True) -> Dict:
    asyncio.create_task(run_full_scrape(db, max_companies, use_ai))
    return {"status": "started", "message": "Scraping job started in background"}
