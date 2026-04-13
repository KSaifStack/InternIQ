"""
Company Source Module - Fetches companies from SimplifyJobs repository
"""
import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import Company

# SimplifyJobs repository URL
GITHUB_API_URL = "https://api.github.com/repos/SimplifyJobs/Summer2026-Internships/contents"

# Fallback static list of top companies with known career pages
# This is used if GitHub API fails or rate limited
DEFAULT_COMPANIES = [
    {"name": "Google", "career_url": "https://careers.google.com/jobs/", "ats_provider": "Greenhouse"},
    {"name": "Meta", "career_url": "https://www.metacareers.com/jobs/", "ats_provider": "Workday"},
    {"name": "Apple", "career_url": "https://jobs.apple.com/", "ats_provider": "Custom"},
    {"name": "Amazon", "career_url": "https://www.amazon.jobs/", "ats_provider": "Custom"},
    {"name": "Microsoft", "career_url": "https://careers.microsoft.com/", "ats_provider": "Lever"},
    {"name": "Netflix", "career_url": "https://jobs.netflix.com/", "ats_provider": "Greenhouse"},
    {"name": "NVIDIA", "career_url": "https://nvidia.wd5.myworkdayjobs.com/", "ats_provider": "Workday"},
    {"name": "Stripe", "career_url": "https://stripe.com/jobs", "ats_provider": "Greenhouse"},
    {"name": "Airbnb", "career_url": "https://airbnb.com/careers", "ats_provider": "Lever"},
    {"name": "Lyft", "career_url": "https://www.lyft.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Uber", "career_url": "https://www.uber.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Salesforce", "career_url": "https://careers.salesforce.com/", "ats_provider": "Custom"},
    {"name": "Adobe", "career_url": "https://www.adobe.com/careers.html", "ats_provider": "Greenhouse"},
    {"name": "Goldman Sachs", "career_url": "https://www.goldmansachs.com/careers/", "ats_provider": "Custom"},
    {"name": "Morgan Stanley", "career_url": "https://www.morganstanley.com/careers/", "ats_provider": "Custom"},
    {"name": "Jane Street", "career_url": "https://www.janestreet.com/jobs/", "ats_provider": "Custom"},
    {"name": "Two Sigma", "career_url": "https://careers.twosigma.com/", "ats_provider": "Greenhouse"},
    {"name": "DE Shaw", "career_url": "https://www.deshaw.com/careers/", "ats_provider": "Custom"},
    {"name": "Citadel", "career_url": "https://www.citadel.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Citi", "career_url": "https://www.citi.com/careers/", "ats_provider": "Custom"},
    {"name": "Bloomberg", "career_url": "https://www.bloomberg.com/careers/", "ats_provider": "Custom"},
    {"name": "Dropbox", "career_url": "https://www.dropbox.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Snap", "career_url": "https://snap.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Pinterest", "career_url": "https://careers.pinterest.com/", "ats_provider": "Greenhouse"},
    {"name": "Twitter", "career_url": "https://careers.twitter.com/", "ats_provider": "Greenhouse"},
    {"name": "LinkedIn", "career_url": "https://careers.linkedin.com/", "ats_provider": "Custom"},
    {"name": "Slack", "career_url": "https://slack.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Square", "career_url": "https://squareup.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Coinbase", "career_url": "https://www.coinbase.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Robinhood", "career_url": "https://robinhood.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Figma", "career_url": "https://www.figma.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Notion", "career_url": "https://notion.so/careers", "ats_provider": "Lever"},
    {"name": "Discord", "career_url": "https://discord.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Spotify", "career_url": "https://www.spotify.com/us/jobs/", "ats_provider": "Greenhouse"},
    {"name": "Twitch", "career_url": "https://www.twitch.tv/en/careers", "ats_provider": "Custom"},
    {"name": "Shopify", "career_url": "https://www.shopify.com/careers", "ats_provider": "Custom"},
    {"name": "Atlassian", "career_url": "https://www.atlassian.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Atlassian (Jira)", "career_url": "https://www.atlassian.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Databricks", "career_url": "https://www.databricks.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Snowflake", "career_url": "https://careers.snowflake.com/", "ats_provider": "Greenhouse"},
    {"name": "Palantir", "career_url": "https://www.palantir.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Rubrik", "career_url": "https://www.rubrik.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "CrowdStrike", "career_url": "https://www.crowdstrike.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Cloudflare", "career_url": "https://www.cloudflare.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Okta", "career_url": "https://www.okta.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Zoom", "career_url": "https://zoom.us/careers", "ats_provider": "Greenhouse"},
    {"name": "DoorDash", "career_url": "https://doordash.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Instacart", "career_url": "https://www.instacart.com/careers/", "ats_provider": "Greenhouse"},
    {"name": "Yelp", "career_url": "https://www.yelp.com/careers", "ats_provider": "Greenhouse"},
    {"name": "Box", "career_url": "https://www.box.com/careers", "ats_provider": "Greenhouse"},
]


def fetch_simplifyjobs_companies() -> List[Dict]:
    """
    Fetch company list from SimplifyJobs GitHub repository.
    Returns a list of company dictionaries.
    """
    try:
        # Try to fetch from GitHub API
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        contents = response.json()

        # Look for README or companies file
        for item in contents:
            if "readme" in item["name"].lower() or "company" in item["name"].lower():
                # Get raw content
                raw_url = item.get("download_url")
                if raw_url:
                    readme_response = requests.get(raw_url, timeout=10)
                    # Parse the markdown to extract companies
                    # For now, return empty and use fallback
                    pass

        return []
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        return []


def get_career_url_for_company(company_name: str) -> Optional[str]:
    """
    Get the career page URL for a company.
    Uses a mapping of known company URLs.
    """
    # Try to find in default companies
    for company in DEFAULT_COMPANIES:
        if company["name"].lower() == company_name.lower():
            return company["career_url"]
    return None


def get_ats_provider(company_name: str) -> Optional[str]:
    """
    Get the ATS provider for a company based on known mappings.
    """
    for company in DEFAULT_COMPANIES:
        if company["name"].lower() == company_name.lower():
            return company.get("ats_provider")
    return None


def sync_companies_to_db(db: Session) -> int:
    """
    Sync companies from SimplifyJobs to the database.
    Returns the number of companies added.
    """
    companies_to_add = []
    existing_companies = {c.name for c in db.query(Company).all()}

    for company_data in DEFAULT_COMPANIES:
        name = company_data["name"]
        if name not in existing_companies:
            companies_to_add.append(Company(
                name=name,
                website_url=company_data.get("career_url"),
                ats_provider=company_data.get("ats_provider")
            ))

    if companies_to_add:
        db.bulk_save_objects(companies_to_add)
        db.commit()

    return len(companies_to_add)


def get_all_companies_from_db(db: Session) -> List[Company]:
    """
    Get all companies from the database.
    """
    return db.query(Company).all()


def get_company_by_name(db: Session, name: str) -> Optional[Company]:
    """
    Get a company by name from the database.
    """
    return db.query(Company).filter(Company.name == name).first()
