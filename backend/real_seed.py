import urllib.request
import json
import logging
from sqlalchemy.orm import Session
from backend.models.database import engine, Base, SessionLocal
from backend.models.models import User, Company, JobListing, Application, SearchLog
from backend.scrapers.deduplicator import generate_listing_hash
from backend.scrapers.ai_job_parser import tag_job_listing, extract_pay_range, detect_work_mode
from datetime import datetime
import re
import requests
import concurrent.futures

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
EXPIRED_KEYWORDS = ["closed", "no longer accepting", "filled", "expired", "404", "not found", "no longer available"]

# Global session and cache for performance
VERIFY_SESSION = requests.Session()
VERIFY_SESSION.headers.update(HEADERS)
VERIFY_CACHE = {}

logging.basicConfig(level=logging.INFO)

GREENHOUSE_BOARDS = [
    ("Stripe", "stripe", "mid_size_tech"),
    ("Airbnb", "airbnb", "mid_size_tech"),
    ("Discord", "discord", "startup"),
    ("Pinterest", "pinterest", "mid_size_tech"),
    ("Reddit", "reddit", "mid_size_tech"),
    ("Twitch", "twitch", "mid_size_tech"),
    ("Cloudflare", "cloudflare", "cloud_infra"),
    ("Roblox", "roblox", "gaming"),
    ("Figma", "figma", "startup"),
    ("AssetMark", "assetmark", "finance"),
    ("FDM Group", "fdmgroup", "consulting"),
]

LEVER_BOARDS = [
    ("Palantir", "palantir", "defense"),
    ("Brooksource", "brooksource", "staffing"),
    ("EPI-USE", "epiuse", "consulting"),
]

def init_db():
    # Base.metadata.drop_all(bind=engine) # Don't drop every time
    Base.metadata.create_all(bind=engine)
    logging.info("Database checked/initialized.")

def extract_state(location_str):
    if not location_str:
        return None
    state_match = re.search(r'\b([A-Z]{2})\b', location_str)
    if state_match:
        state = state_match.group(1)
        valid = ["CA","NY","TX","WA","MA","IL","GA","CO","NC","FL","PA","OH","VA","OR","MI","AZ","MN","MD","CT","NJ"]
        if state in valid:
            return state
    if "remote" in location_str.lower():
        return None
    return None

def is_intern_role(title):
    """Focus strictly on university/intern/entry-level roles. Exclude Senior/Staff/Lead."""
    t = title.lower()
    # Explicit exclusions
    if any(ex in t for ex in ["senior", "staff", "principal", "manager", "lead", "sr.", "head", "director", "vp"]):
        return False
    # Explicit inclusions
    if any(inc in t for inc in ["intern", "university", "junior", "associate", "new grad", "apprentice", "fellowship"]):
        return True
    return False

def fetch_greenhouse_jobs(board_name, db_company_id, company_name):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_name}/jobs"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    jobs = []
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
            for job in data.get("jobs", []):
                title = job.get("title", "")
                if is_intern_role(title):
                    location = job.get("location", {}).get("name", "Remote")
                    is_remote = "remote" in location.lower()
                    state = extract_state(location)
                    description = title + " role at " + company_name
                    work_mode = detect_work_mode(location + " " + title)
                    tags = tag_job_listing(description, title)
                    listing_hash = generate_listing_hash(company_name, title, location)
                    app_url = job.get("absolute_url", "")

                    jobs.append(JobListing(
                        title=title,
                        description=description,
                        location=location,
                        state=state,
                        is_remote=is_remote,
                        application_url=app_url,
                        required_skills="Python, SQL, React, AWS",
                        company_id=db_company_id,
                        work_mode=work_mode,
                        tags=tags,
                        listing_hash=listing_hash,
                        source_url=url,
                    ))
    except Exception as e:
        logging.warning(f"Failed to fetch Greenhouse for {board_name}: {e}")
    return jobs

def fetch_lever_jobs(board_name, db_company_id, company_name):
    url = f"https://api.lever.co/v0/postings/{board_name}?mode=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    jobs = []
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
            for job in data:
                title = job.get("text", "")
                if is_intern_role(title):
                    location = job.get("categories", {}).get("location", "Remote")
                    is_remote = "remote" in location.lower() or "remote" in title.lower()
                    state = extract_state(location)
                    description = job.get("descriptionPlain", "")[:500] + "..."
                    work_mode = detect_work_mode(location + " " + title + " " + description)
                    tags = tag_job_listing(description, title)
                    listing_hash = generate_listing_hash(company_name, title, location)

                    jobs.append(JobListing(
                        title=title,
                        description=description,
                        location=location,
                        state=state,
                        is_remote=is_remote,
                        application_url=job.get("applyUrl", ""),
                        required_skills="Python, SQL, React, AWS",
                        company_id=db_company_id,
                        work_mode=work_mode,
                        tags=tags,
                        listing_hash=listing_hash,
                        source_url=url,
                    ))
    except Exception as e:
        logging.warning(f"Failed to fetch Lever for {board_name}: {e}")
    return jobs

def is_link_open(url):
    """Deep verification with caching and optimized requests."""
    if not url: return False
    if url in VERIFY_CACHE: return VERIFY_CACHE[url]
    
    try:
        # Try HEAD first for speed
        resp = VERIFY_SESSION.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 404:
            VERIFY_CACHE[url] = False
            return False
        
        # If OK, check content for keywords
        resp = VERIFY_SESSION.get(url, timeout=10, allow_redirects=True)
        if resp.status_code != 200:
            VERIFY_CACHE[url] = False
            return False
            
        text = resp.text.lower()
        for kw in EXPIRED_KEYWORDS:
            if kw in text:
                VERIFY_CACHE[url] = False
                return False
        
        VERIFY_CACHE[url] = True
        return True
    except Exception:
        VERIFY_CACHE[url] = False
        return False

def process_job_batch(db, jobs, company_name, company_id):
    """Process a batch of jobs in parallel (only inserts if is_link_open). Use for verification runs."""
    from backend.scrapers.deduplicator import deduplicate_and_insert

    inserted = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_job = {executor.submit(is_link_open, job.application_url): job for job in jobs}
        for future in concurrent.futures.as_completed(future_to_job):
            job_obj = future_to_job[future]
            try:
                if future.result():
                    job_dict = {
                        "title": job_obj.title,
                        "description": job_obj.description,
                        "location": job_obj.location,
                        "state": job_obj.state,
                        "is_remote": job_obj.is_remote,
                        "application_url": job_obj.application_url,
                        "required_skills": job_obj.required_skills,
                        "work_mode": job_obj.work_mode,
                        "tags": job_obj.tags,
                        "listing_hash": job_obj.listing_hash,
                        "source_url": job_obj.source_url
                    }
                    res = deduplicate_and_insert(db, company_name, job_dict, company_id)
                    if res.get("action") == "inserted":
                        inserted += 1
                else:
                    logging.info(f"Skipping closed job: {job_obj.title} at {company_name}")
            except Exception as e:
                logging.debug(f"Error processing parallel job: {e}")
                continue
    return inserted


def insert_seed_jobs_without_verification(db, jobs, company_name, company_id):
    """Insert all seed jobs without link verification so they appear in the feed; closed detection can run later."""
    from backend.scrapers.deduplicator import deduplicate_and_insert
    inserted = 0
    for job_obj in jobs:
        try:
            job_dict = {
                "title": job_obj.title,
                "description": job_obj.description,
                "location": job_obj.location,
                "state": job_obj.state,
                "is_remote": job_obj.is_remote,
                "application_url": job_obj.application_url,
                "required_skills": job_obj.required_skills,
                "work_mode": job_obj.work_mode,
                "tags": job_obj.tags,
                "listing_hash": job_obj.listing_hash,
                "source_url": job_obj.source_url
            }
            res = deduplicate_and_insert(db, company_name, job_dict, company_id)
            if res.get("action") == "inserted":
                inserted += 1
        except Exception as e:
            logging.debug(f"Error inserting seed job {job_obj.title}: {e}")
    return inserted

def populate_real_data():
    db = SessionLocal()
    from backend.scrapers.deduplicator import deduplicate_and_insert
    
    test_email = "test@student.edu"
    test_user = db.query(User).filter(User.email == test_email).first()
    if not test_user:
        test_user = User(
            email=test_email, full_name="Alice Student",
            graduation_year=2026, skills="Python, React, SQL, Java, Node.js",
            location="CA"
        )
        db.add(test_user)
        db.commit()

    total_jobs = 0
    
    # Check if we already have jobs. If so, skip the heavy seeding and let background sync handle it.
    existing_jobs_count = db.query(JobListing).count()
    if existing_jobs_count > 10:
        logging.info(f"Database already contains {existing_jobs_count} jobs. Skipping heavy initial seeding.")
        db.close()
        return
    
    # 1. Fetch YC Companies
    logging.info("Starting YC Startup discovery...")
    try:
        from backend.scrapers.company_discovery import fetch_yc_companies
        yc_companies = fetch_yc_companies()
        for yc in yc_companies:
            db_company = db.query(Company).filter(Company.name == yc["name"]).first()
            if not db_company:
                db_company = Company(
                    name=yc["name"],
                    category="startup",
                    discovery_source="yc_startup",
                    website_url=yc["website"]
                )
                db.add(db_company)
                db.commit()
                db.refresh(db_company)
    except Exception as e:
        logging.warning(f"YC Discovery skipped: {e}")

    # 1.5 Add Targeted Companies
    targeted = [
        ("Compass Group", "catering"),
        ("Fastenal IT", "industrial"),
        ("Spectrum", "telecom"),
        ("Tata Consultancy Services (TCS)", "consulting"),
        ("NC Dept of Information Technology", "government"),
        ("George Mason University - College of Engineering & Computing", "education"),
        ("College of Computing and Informatics", "education"),
    ]
    for name, cat in targeted:
        co = db.query(Company).filter(Company.name == name).first()
        if not co:
            db.add(Company(name=name, category=cat, discovery_source="seed"))
    db.commit()

    # 2. Fetch greenhouse
    for company_name, board_name, category in GREENHOUSE_BOARDS:
        db_company = db.query(Company).filter(Company.name == company_name).first()
        if not db_company:
            db_company = Company(
                name=company_name, ats_provider="Greenhouse",
                category=category, discovery_source="seed",
                career_url=f"https://boards.greenhouse.io/{board_name}",
            )
            db.add(db_company)
            db.commit()
            db.refresh(db_company)
        
        jobs = fetch_greenhouse_jobs(board_name, db_company.id, company_name)
        inserted_for_co = insert_seed_jobs_without_verification(db, jobs, company_name, db_company.id)
        if inserted_for_co > 0:
            total_jobs += inserted_for_co
            logging.info(f"Added {inserted_for_co} new intern jobs for {company_name}")

    # Fetch Lever
    for company_name, board_name, category in LEVER_BOARDS:
        db_company = db.query(Company).filter(Company.name == company_name).first()
        if not db_company:
            db_company = Company(
                name=company_name, ats_provider="Lever",
                category=category, discovery_source="seed",
                career_url=f"https://jobs.lever.co/{board_name}",
            )
            db.add(db_company)
            db.commit()
            db.refresh(db_company)
        
        jobs = fetch_lever_jobs(board_name, db_company.id, company_name)
        inserted_for_co = insert_seed_jobs_without_verification(db, jobs, company_name, db_company.id)
        if inserted_for_co > 0:
            total_jobs += inserted_for_co
            logging.info(f"Added {inserted_for_co} new intern jobs for {company_name}")
            
    db.close()
    logging.info(f"Real data population sync complete. {total_jobs} new jobs added.")

def run_greenhouse_scraper(db: Session) -> dict:
    """
    Run Greenhouse scraper for all GREENHOUSE_BOARDS. Used by scraper_runner.
    Returns {"added": N, "source": "greenhouse"}. One company failure does not stop the rest.
    """
    import time
    total_added = 0
    for company_name, board_name, category in GREENHOUSE_BOARDS:
        try:
            time.sleep(1.5)
            db_company = db.query(Company).filter(Company.name == company_name).first()
            if not db_company:
                db_company = Company(
                    name=company_name, ats_provider="Greenhouse",
                    category=category, discovery_source="seed",
                    career_url=f"https://boards.greenhouse.io/{board_name}",
                )
                db.add(db_company)
                db.commit()
                db.refresh(db_company)
            jobs = fetch_greenhouse_jobs(board_name, db_company.id, company_name)
            total_added += insert_seed_jobs_without_verification(db, jobs, company_name, db_company.id)
        except Exception as e:
            logging.warning("Greenhouse scraper failed for %s: %s", company_name, e)
    return {"added": total_added, "source": "greenhouse"}


def run_lever_scraper(db: Session) -> dict:
    """
    Run Lever scraper for all LEVER_BOARDS. Used by scraper_runner.
    Returns {"added": N, "source": "lever"}. One company failure does not stop the rest.
    """
    import time
    total_added = 0
    for company_name, board_name, category in LEVER_BOARDS:
        try:
            time.sleep(1.5)
            db_company = db.query(Company).filter(Company.name == company_name).first()
            if not db_company:
                db_company = Company(
                    name=company_name, ats_provider="Lever",
                    category=category, discovery_source="seed",
                    career_url=f"https://jobs.lever.co/{board_name}",
                )
                db.add(db_company)
                db.commit()
                db.refresh(db_company)
            jobs = fetch_lever_jobs(board_name, db_company.id, company_name)
            total_added += insert_seed_jobs_without_verification(db, jobs, company_name, db_company.id)
        except Exception as e:
            logging.warning("Lever scraper failed for %s: %s", company_name, e)
    return {"added": total_added, "source": "lever"}


if __name__ == "__main__":
    init_db()
    populate_real_data()
