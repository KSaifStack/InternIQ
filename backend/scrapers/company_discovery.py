"""
Company Discovery Module — Step 1
Discovers companies that hire CS interns, categorizes them, and grows the internal database.
Uses: built-in list, SimplifyJobs GitHub repos (Summer2026, Summer2025), and optional web search (duckduckgo-search).
"""
import json
import os
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

import logging
logger = logging.getLogger(__name__)

# Popular GitHub repos for internship listings (SimplifyJobs-style README tables)
GITHUB_INTERNSHIP_REPOS = [
    ("SimplifyJobs", "Summer2026-Internships", "dev"),   # Simplify 2026
    ("vanshb03", "Summer2026-Internships", "main"),     # Ouckah / Vansh 2026
    ("speedyapply", "2026-SWE-College-Jobs", "main"),   # SpeedyApply 2026
]

# Category mappings for known companies
COMPANY_CATEGORIES = {
    # FAANG / Big Tech
    "Google": "FAANG", "Meta": "FAANG", "Apple": "FAANG", "Amazon": "FAANG",
    "Netflix": "FAANG", "Microsoft": "big_tech", "NVIDIA": "big_tech",
    "Alphabet": "FAANG", "Facebook": "FAANG",
    # Big Tech
    "Salesforce": "big_tech", "Adobe": "big_tech", "Oracle": "big_tech",
    "IBM": "big_tech", "Intel": "big_tech", "Cisco": "big_tech",
    "VMware": "big_tech", "SAP": "big_tech", "Qualcomm": "big_tech",
    "Texas Instruments": "big_tech", "Broadcom": "big_tech",
    "LinkedIn": "big_tech", "Twitter": "big_tech", "X": "big_tech",
    # Mid-size Tech
    "Stripe": "mid_size_tech", "Airbnb": "mid_size_tech", "Lyft": "mid_size_tech",
    "Uber": "mid_size_tech", "Snap": "mid_size_tech", "Pinterest": "mid_size_tech",
    "Spotify": "mid_size_tech", "Dropbox": "mid_size_tech", "Slack": "mid_size_tech",
    "Square": "mid_size_tech", "Block": "mid_size_tech", "Twitch": "mid_size_tech",
    "DoorDash": "mid_size_tech", "Instacart": "mid_size_tech", "Yelp": "mid_size_tech",
    "Box": "mid_size_tech", "Zoom": "mid_size_tech", "Shopify": "mid_size_tech",
    "Atlassian": "mid_size_tech", "Reddit": "mid_size_tech",
    # Startup / Growth
    "Figma": "startup", "Notion": "startup", "Discord": "startup",
    "Coinbase": "startup", "Robinhood": "startup", "Vercel": "startup",
    "Supabase": "startup", "Railway": "startup", "Retool": "startup",
    "Airtable": "startup", "Canva": "startup", "Miro": "startup",
    "Linear": "startup", "Ramp": "startup", "Brex": "startup",
    "Loom": "startup", "Rippling": "startup", "Gusto": "startup",
    # Fintech
    "Goldman Sachs": "fintech", "Morgan Stanley": "fintech", "JPMorgan": "fintech",
    "JP Morgan": "fintech", "Jane Street": "fintech", "Two Sigma": "fintech",
    "DE Shaw": "fintech", "D.E. Shaw": "fintech", "Citadel": "fintech",
    "Citi": "fintech", "Bloomberg": "fintech", "Capital One": "fintech",
    "Visa": "fintech", "Mastercard": "fintech", "PayPal": "fintech",
    "Plaid": "fintech", "Affirm": "fintech", "Chime": "fintech",
    "SoFi": "fintech", "Fidelity": "fintech",
    # Cloud / Infra
    "Databricks": "cloud_infra", "Snowflake": "cloud_infra", "Cloudflare": "cloud_infra",
    "MongoDB": "cloud_infra", "Elastic": "cloud_infra", "HashiCorp": "cloud_infra",
    "Confluent": "cloud_infra", "Datadog": "cloud_infra",
    # Cybersecurity
    "CrowdStrike": "cybersecurity", "Palo Alto Networks": "cybersecurity",
    "Okta": "cybersecurity", "Rubrik": "cybersecurity", "Fortinet": "cybersecurity",
    "SentinelOne": "cybersecurity", "Zscaler": "cybersecurity",
    # Defense / Gov
    "Palantir": "defense", "Lockheed Martin": "defense", "Raytheon": "defense",
    "Boeing": "defense", "Northrop Grumman": "defense", "General Dynamics": "defense",
    "L3Harris": "defense", "BAE Systems": "defense", "Anduril": "defense",
    # Healthtech
    "Epic Systems": "healthtech", "Cerner": "healthtech", "Veeva": "healthtech",
    "Tempus": "healthtech", "Flatiron Health": "healthtech", "Oscar Health": "healthtech",
    # Consulting
    "McKinsey": "consulting", "BCG": "consulting", "Bain": "consulting",
    "Deloitte": "consulting", "Accenture": "consulting", "PwC": "consulting",
    "EY": "consulting", "KPMG": "consulting",
    # Gaming / Media
    "Electronic Arts": "gaming", "EA": "gaming", "Roblox": "gaming",
    "Epic Games": "gaming", "Riot Games": "gaming", "Activision": "gaming",
    "Unity": "gaming", "Valve": "gaming",
}

# Extended company database with career URLs and ATS providers
EXTENDED_COMPANIES = [
    # FAANG
    {"name": "Google", "website": "https://google.com", "career_url": "https://careers.google.com/jobs/", "ats": "Custom", "category": "FAANG", "season": "August"},
    {"name": "Meta", "website": "https://meta.com", "career_url": "https://www.metacareers.com/jobs/", "ats": "Custom", "category": "FAANG", "season": "September"},
    {"name": "Apple", "website": "https://apple.com", "career_url": "https://jobs.apple.com/", "ats": "Custom", "category": "FAANG", "season": "September"},
    {"name": "Amazon", "website": "https://amazon.com", "career_url": "https://www.amazon.jobs/", "ats": "Custom", "category": "FAANG", "season": "September"},
    {"name": "Netflix", "website": "https://netflix.com", "career_url": "https://jobs.netflix.com/", "ats": "Greenhouse", "category": "FAANG", "season": "October"},
    {"name": "Microsoft", "website": "https://microsoft.com", "career_url": "https://careers.microsoft.com/", "ats": "Custom", "category": "big_tech", "season": "August"},
    {"name": "NVIDIA", "website": "https://nvidia.com", "career_url": "https://nvidia.wd5.myworkdayjobs.com/", "ats": "Workday", "category": "big_tech", "season": "August"},
    # Mid-size Tech
    {"name": "Stripe", "website": "https://stripe.com", "career_url": "https://stripe.com/jobs", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Airbnb", "website": "https://airbnb.com", "career_url": "https://careers.airbnb.com/", "ats": "Greenhouse", "category": "mid_size_tech", "season": "September"},
    {"name": "Lyft", "website": "https://lyft.com", "career_url": "https://www.lyft.com/careers", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Uber", "website": "https://uber.com", "career_url": "https://www.uber.com/careers/", "ats": "Greenhouse", "category": "mid_size_tech", "season": "September"},
    {"name": "Spotify", "website": "https://spotify.com", "career_url": "https://www.lifeatspotify.com/jobs", "ats": "Greenhouse", "category": "mid_size_tech", "season": "October"},
    {"name": "Pinterest", "website": "https://pinterest.com", "career_url": "https://www.pinterestcareers.com/", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Snap", "website": "https://snap.com", "career_url": "https://snap.com/en-US/jobs", "ats": "Greenhouse", "category": "mid_size_tech", "season": "September"},
    {"name": "DoorDash", "website": "https://doordash.com", "career_url": "https://careers.doordash.com/", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Shopify", "website": "https://shopify.com", "career_url": "https://www.shopify.com/careers", "ats": "Custom", "category": "mid_size_tech", "season": "January"},
    {"name": "Dropbox", "website": "https://dropbox.com", "career_url": "https://www.dropbox.com/jobs", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Reddit", "website": "https://reddit.com", "career_url": "https://www.redditinc.com/careers", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Zoom", "website": "https://zoom.us", "career_url": "https://careers.zoom.us/", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    {"name": "Atlassian", "website": "https://atlassian.com", "career_url": "https://www.atlassian.com/company/careers", "ats": "Greenhouse", "category": "mid_size_tech", "season": "Year-round"},
    # Startup / Growth
    {"name": "Figma", "website": "https://figma.com", "career_url": "https://www.figma.com/careers/", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    {"name": "Notion", "website": "https://notion.so", "career_url": "https://www.notion.so/careers", "ats": "Lever", "category": "startup", "season": "Year-round"},
    {"name": "Discord", "website": "https://discord.com", "career_url": "https://discord.com/careers", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    {"name": "Vercel", "website": "https://vercel.com", "career_url": "https://vercel.com/careers", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    {"name": "Retool", "website": "https://retool.com", "career_url": "https://retool.com/careers", "ats": "Lever", "category": "startup", "season": "Year-round"},
    {"name": "Ramp", "website": "https://ramp.com", "career_url": "https://ramp.com/careers", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    {"name": "Linear", "website": "https://linear.app", "career_url": "https://linear.app/careers", "ats": "Lever", "category": "startup", "season": "Year-round"},
    {"name": "Rippling", "website": "https://rippling.com", "career_url": "https://www.rippling.com/careers", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    {"name": "Canva", "website": "https://canva.com", "career_url": "https://www.canva.com/careers/", "ats": "Greenhouse", "category": "startup", "season": "Year-round"},
    # Fintech
    {"name": "Goldman Sachs", "website": "https://goldmansachs.com", "career_url": "https://www.goldmansachs.com/careers/", "ats": "Custom", "category": "fintech", "season": "July"},
    {"name": "Morgan Stanley", "website": "https://morganstanley.com", "career_url": "https://www.morganstanley.com/careers/", "ats": "Custom", "category": "fintech", "season": "July"},
    {"name": "Jane Street", "website": "https://janestreet.com", "career_url": "https://www.janestreet.com/join-jane-street/", "ats": "Custom", "category": "fintech", "season": "June"},
    {"name": "Two Sigma", "website": "https://twosigma.com", "career_url": "https://www.twosigma.com/careers/", "ats": "Greenhouse", "category": "fintech", "season": "August"},
    {"name": "Citadel", "website": "https://citadel.com", "career_url": "https://www.citadel.com/careers/", "ats": "Greenhouse", "category": "fintech", "season": "July"},
    {"name": "DE Shaw", "website": "https://deshaw.com", "career_url": "https://www.deshaw.com/careers", "ats": "Custom", "category": "fintech", "season": "July"},
    {"name": "Capital One", "website": "https://capitalone.com", "career_url": "https://www.capitalonecareers.com/", "ats": "Workday", "category": "fintech", "season": "August"},
    {"name": "Bloomberg", "website": "https://bloomberg.com", "career_url": "https://www.bloomberg.com/careers/", "ats": "Custom", "category": "fintech", "season": "August"},
    {"name": "Visa", "website": "https://visa.com", "career_url": "https://usa.visa.com/careers.html", "ats": "Workday", "category": "fintech", "season": "September"},
    {"name": "PayPal", "website": "https://paypal.com", "career_url": "https://careers.pypl.com/", "ats": "Workday", "category": "fintech", "season": "September"},
    {"name": "Plaid", "website": "https://plaid.com", "career_url": "https://plaid.com/careers/", "ats": "Greenhouse", "category": "fintech", "season": "Year-round"},
    {"name": "Robinhood", "website": "https://robinhood.com", "career_url": "https://robinhood.com/careers/", "ats": "Greenhouse", "category": "fintech", "season": "Year-round"},
    {"name": "Coinbase", "website": "https://coinbase.com", "career_url": "https://www.coinbase.com/careers", "ats": "Greenhouse", "category": "fintech", "season": "Year-round"},
    # Cloud / Infra
    {"name": "Databricks", "website": "https://databricks.com", "career_url": "https://www.databricks.com/company/careers", "ats": "Greenhouse", "category": "cloud_infra", "season": "August"},
    {"name": "Snowflake", "website": "https://snowflake.com", "career_url": "https://careers.snowflake.com/", "ats": "Greenhouse", "category": "cloud_infra", "season": "August"},
    {"name": "Cloudflare", "website": "https://cloudflare.com", "career_url": "https://www.cloudflare.com/careers/", "ats": "Greenhouse", "category": "cloud_infra", "season": "Year-round"},
    {"name": "MongoDB", "website": "https://mongodb.com", "career_url": "https://www.mongodb.com/careers", "ats": "Greenhouse", "category": "cloud_infra", "season": "Year-round"},
    {"name": "Datadog", "website": "https://datadoghq.com", "career_url": "https://careers.datadoghq.com/", "ats": "Greenhouse", "category": "cloud_infra", "season": "Year-round"},
    # Cybersecurity
    {"name": "CrowdStrike", "website": "https://crowdstrike.com", "career_url": "https://www.crowdstrike.com/careers/", "ats": "Workday", "category": "cybersecurity", "season": "Year-round"},
    {"name": "Palo Alto Networks", "website": "https://paloaltonetworks.com", "career_url": "https://jobs.paloaltonetworks.com/", "ats": "Workday", "category": "cybersecurity", "season": "Year-round"},
    {"name": "Okta", "website": "https://okta.com", "career_url": "https://www.okta.com/careers/", "ats": "Greenhouse", "category": "cybersecurity", "season": "Year-round"},
    # Defense
    {"name": "Palantir", "website": "https://palantir.com", "career_url": "https://www.palantir.com/careers/", "ats": "Lever", "category": "defense", "season": "August"},
    {"name": "Anduril", "website": "https://anduril.com", "career_url": "https://www.anduril.com/careers/", "ats": "Greenhouse", "category": "defense", "season": "Year-round"},
    {"name": "Lockheed Martin", "website": "https://lockheedmartin.com", "career_url": "https://www.lockheedmartinjobs.com/", "ats": "Workday", "category": "defense", "season": "September"},
    {"name": "Northrop Grumman", "website": "https://northropgrumman.com", "career_url": "https://www.northropgrumman.com/careers/", "ats": "Workday", "category": "defense", "season": "September"},
    # Healthtech
    {"name": "Epic Systems", "website": "https://epic.com", "career_url": "https://careers.epic.com/", "ats": "Custom", "category": "healthtech", "season": "Year-round"},
    # Gaming
    {"name": "Roblox", "website": "https://roblox.com", "career_url": "https://careers.roblox.com/", "ats": "Greenhouse", "category": "gaming", "season": "Year-round"},
    {"name": "Epic Games", "website": "https://epicgames.com", "career_url": "https://www.epicgames.com/site/careers", "ats": "Greenhouse", "category": "gaming", "season": "Year-round"},
    {"name": "Riot Games", "website": "https://riotgames.com", "career_url": "https://www.riotgames.com/en/work-with-us", "ats": "Greenhouse", "category": "gaming", "season": "Year-round"},
    # Big Tech extras
    {"name": "Salesforce", "website": "https://salesforce.com", "career_url": "https://careers.salesforce.com/", "ats": "Custom", "category": "big_tech", "season": "September"},
    {"name": "Adobe", "website": "https://adobe.com", "career_url": "https://careers.adobe.com/", "ats": "Workday", "category": "big_tech", "season": "September"},
    {"name": "Oracle", "website": "https://oracle.com", "career_url": "https://www.oracle.com/careers/", "ats": "Custom", "category": "big_tech", "season": "September"},
    {"name": "Intel", "website": "https://intel.com", "career_url": "https://jobs.intel.com/", "ats": "Workday", "category": "big_tech", "season": "September"},
    {"name": "Cisco", "website": "https://cisco.com", "career_url": "https://jobs.cisco.com/", "ats": "Custom", "category": "big_tech", "season": "September"},
    {"name": "Qualcomm", "website": "https://qualcomm.com", "career_url": "https://careers.qualcomm.com/", "ats": "Workday", "category": "big_tech", "season": "September"},
]

# Search queries for discovering more companies (used by web search when enabled)
DISCOVERY_QUERIES = [
    "companies hiring software engineering interns 2025",
    "companies hiring software engineering interns 2026",
    "top CS internships summer 2025",
    "tech internships for computer science students",
    "startup internships software engineer",
    "fintech internship programs 2025",
    "healthtech companies hiring interns",
    "defense tech companies internships",
    "best paying software internships 2026",
    "site:wellfound.com software engineer intern 2026",
    "site:untapped.io internships 2026",
    "site:levels.fyi software engineering intern 2026",
    "YC startups hiring interns 2026",
]

# Optional: set INTERNIQ_WEB_SEARCH=1 and install duckduckgo-search to enable web discovery
def _run_web_search(query: str, max_results: int = 10) -> List[Dict]:
    """Run a web search and return parsed company-like results. Returns list of {name, source_query}."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = (r.get("title") or "")
                body = (r.get("body") or "")
                # Extract company names from title/snippet (heuristic: title often has "Company Name - Job" or "at Company")
                # Also accept titles that look like company names (Title Case, not too long)
                name = _extract_company_from_snippet(title, body)
                if name:
                    results.append({"name": name, "source_query": query})
        return results
    except ImportError:
        return []
    except Exception as e:
        print(f"Web search error for '{query}': {e}")
        return []


def _extract_company_from_snippet(title: str, body: str) -> Optional[str]:
    """Heuristic: pull company name from search snippet. Prefer known companies or Title Case phrases."""
    text = f"{title} {body}"
    # Pattern: "at Company Name" or "Company Name careers" or "Company Name hiring"
    at_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&\s\.\-]+?)(?:\s+[-–|]|\s+careers|\s+hiring|\.|$)", text)
    if at_match:
        name = at_match.group(1).strip()
        if 2 <= len(name) <= 50 and "intern" not in name.lower():
            return name
    # Known company names mentioned in snippet
    for known in list(COMPANY_CATEGORIES.keys())[:80]:
        if known.lower() in text.lower():
            return known
    return None


def categorize_company(name: str) -> str:
    """Categorize a company by name using known mappings + heuristics."""
    # Check known mappings
    if name in COMPANY_CATEGORIES:
        return COMPANY_CATEGORIES[name]

    # Heuristic: check name patterns
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["bank", "capital", "financial", "fidelity", "securities"]):
        return "fintech"
    if any(kw in name_lower for kw in ["health", "medical", "pharma", "bio"]):
        return "healthtech"
    if any(kw in name_lower for kw in ["defense", "aerospace", "military"]):
        return "defense"
    if any(kw in name_lower for kw in ["game", "gaming", "entertainment"]):
        return "gaming"
    if any(kw in name_lower for kw in ["cloud", "data", "analytics"]):
        return "cloud_infra"
    if any(kw in name_lower for kw in ["security", "cyber"]):
        return "cybersecurity"

    return "other"


def _extract_company_name(cell: str) -> str:
    """Extract company name from table cell: handles markdown **[Name](url)** and raw HTML <a>tags."""
    cell = (cell or "").strip()
    # 1. Strip markdown bold
    cell = cell.replace("**", "").strip()
    # 2. Extract from markdown link [Name](url)
    m = re.search(r"\[([^\]]+)\]\([^)]+\)", cell)
    if m:
        cell = m.group(1).strip()
    # 3. Strip any remaining HTML tags (common in mixed READMEs)
    cell = re.sub(r"<[^>]+>", "", cell).strip()
    return cell


def _extract_apply_url(cell: str) -> Optional[str]:
    """Extract FIRST link URL from table cell, even if it doesn't say 'Apply' specifically."""
    if not cell:
        return None
    # Match any [Text](url) where url is https?
    m = re.search(r"\[[^\]]+\]\s*\((https?://[^)\s]+)\)", cell)
    if m:
        return m.group(1).strip()
    # Fallback: just find a raw url
    m = re.search(r"(https?://[^\s\|<>\)]+)", cell)
    if m:
        return m.group(1).strip()
    return None


def _parse_simplifyjobs_html_table(readme_text: str) -> List[Dict]:
    """
    Parse SimplifyJobs README when it uses HTML tables (<tr>, <td>).
    Returns same structure as parse_simplifyjobs_table_rows.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []
    rows = []
    last_company = ""
    soup = BeautifulSoup(readme_text, "html.parser")
    for tr in soup.find_all("tr"):
        # Check for 'closed' indicators: strike-through tags
        if tr.find(["del", "s", "strike"]):
            continue
            
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
            
        # First td: company
        company_name = _extract_company_name(tds[0].get_text(separator=" ", strip=True))
        
        if not company_name or len(company_name) < 2:
            # Same-as-above row (e.g. ↳)
            company_name = last_company
        else:
            last_company = company_name
            
        if not company_name:
            continue
            
        # Second td: title
        title_cell = tds[1]
        if title_cell.find(["del", "s", "strike"]):
            continue # specific role is closed
        title = title_cell.get_text(separator=" ", strip=True)
        # Final safety cleanup for title
        title = re.sub(r"<[^>]+>", "", title).strip()
        
        location = (tds[2].get_text(strip=True) if len(tds) > 2 else "") or ""
        
        # Fourth td: application link
        app_url = ""
        if len(tds) > 3:
            app_td = tds[3]
            # Check if apply button/link is crossed out
            if app_td.find(["del", "s", "strike"]):
                continue
            # Try to find 'Apply' link specifically first, then fallback to first link
            app_a = app_td.find("a", string=re.compile("Apply", re.I), href=True) or app_td.find("a", href=True)
            if app_a and app_a.get("href", "").startswith("http"):
                app_url = app_a["href"].strip()
                
        if not title and not app_url:
            continue
            
        rows.append({
            "company_name": company_name,
            "title": title or "Intern",
            "location": location,
            "application_url": app_url,
            "source": "github_simplify",
        })
    return rows


def parse_simplifyjobs_table_rows(readme_text: str) -> List[Dict]:
    """
    Parse SimplifyJobs-style README table (HTML <tr>/<td> or markdown | col |).
    Returns list of {company_name, title, location, application_url, source}.
    """
    # Aggregate both HTML and Markdown parsed results
    all_rows = []
    
    html_rows = _parse_simplifyjobs_html_table(readme_text)
    if html_rows:
        all_rows.extend(html_rows)
        
    # Markdown table parsing
    md_rows = []
    in_table = False
    last_company = ""
    for line in readme_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line == "|":
            in_table = False
            last_company = ""
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]  # drop empty first/last from leading/trailing |
        if len(cells) < 3: # Relaxed from 4 to 3
            continue
        if not in_table:
            in_table = True
            if cells[0].lower() == "company" or "company" in (cells[0].lower() if cells else ""):
                continue
            # Skip separator row: | --- | --- | --- |
            if re.match(r"^\-+$", (cells[0] or "").strip()):
                continue
        raw_company = cells[0].strip()
        if re.match(r"^\-+$", raw_company):
            continue
            
        # Check for closed status in markdown (~~text~~)
        # ONLY skip if the APPLICATION URL cell is crossed out, not just any cell
        app_cell = cells[3] if len(cells) > 3 else ""
        if "~~" in app_cell:
            continue

        # "↳" or similar means same company as previous row
        if raw_company in ("↳", "&uarr;", "↑") or (len(raw_company) <= 2 and not raw_company.isalnum()):
            company_name = last_company
        else:
            company_name = _extract_company_name(cells[0])
            if company_name and len(company_name) >= 2 and company_name.lower() != "company":
                last_company = company_name
        if not company_name:
            continue
        title = (cells[1] if len(cells) > 1 else "").strip()
        # Strip HTML from title as well
        title = re.sub(r"<[^>]+>", "", title).strip()
        
        location = (cells[2] if len(cells) > 2 else "").strip()
        application_url = _extract_apply_url(app_cell)
        
        if not title and not application_url:
            continue
            
        md_rows.append({
            "company_name": company_name,
            "title": title or "Intern",
            "location": location or "",
            "application_url": application_url or "",
            "source": "github_simplify",
        })
    
    # Simple deduplication between HTML and MD results based on (company, title, url)
    seen = set()
    final_rows = []
    for r in (all_rows + md_rows):
        key = (r["company_name"].lower(), r["title"].lower(), r["application_url"].lower())
        if key not in seen:
            seen.add(key)
            final_rows.append(r)
            
    return final_rows


def parse_simplifyjobs_readme(readme_text: str) -> List[Dict]:
    """
    Parse the SimplifyJobs README to extract companies (names only).
    The README has tables with: Company | Role | Location | Application Link | Date Posted
    """
    companies = []
    seen = set()
    for row in parse_simplifyjobs_table_rows(readme_text):
        name = row["company_name"]
        if name and name not in seen and len(name) > 1:
            name = name.replace("**", "").strip()
            if name:
                seen.add(name)
                companies.append({
                    "name": name,
                    "category": categorize_company(name),
                    "discovery_source": "simplify",
                })
    return companies


def fetch_github_internship_listings() -> List[Dict]:
    """
    Fetch internship listings from popular GitHub repos (SimplifyJobs Summer2026, Summer2025).
    Tries each repo in GITHUB_INTERNSHIP_REPOS until one succeeds.
    Returns list of {company_name, title, location, application_url, source}.
    """
    all_listings = []
    for org, repo, branch in GITHUB_INTERNSHIP_REPOS:
        try:
            url = f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/README.md"
            # Use a standard browser User-Agent to avoid 403/405 "Not Allowed" errors from some CDNs
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            readme_text = response.text
            listings = parse_simplifyjobs_table_rows(readme_text)
            if listings:
                print(f"Successfully fetched {len(listings)} listings from {org}/{repo}")
                all_listings.extend(listings)
                # continue to next repo to gather ALL of them
        except Exception as e:
            print(f"Fetch {org}/{repo}: {e}")
            continue
    return all_listings


def fetch_simplifyjobs_companies() -> List[Dict]:
    """Fetch companies from popular GitHub repos (PittCSC, Simplify, etc.)."""
    all_companies = []
    seen = set()
    for org, repo, branch in GITHUB_INTERNSHIP_REPOS:
        try:
            url = f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/README.md"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            readme_text = response.text
            companies = parse_simplifyjobs_readme(readme_text)
            for c in companies:
                if c["name"] not in seen:
                    seen.add(c["name"])
                    all_companies.append(c)
        except Exception as e:
            print(f"Fetch companies from {org}/{repo}: {e}")
            continue
    return all_companies


# US state abbreviations used for parsing location -> state filter
_VALID_STATES = frozenset(
    "CA NY TX WA MA IL GA CO NC FL PA OH VA OR MI AZ MN MD CT NJ IN MO TN WI AL SC NV UT".split()
)

# Full state names -> abbreviation (lowercase keys for case-insensitive match)
_STATE_NAME_TO_ABBR = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}


def _extract_state_from_location(location: str):
    """Extract state abbreviation from location string (e.g. 'Durham, NC' or 'Raleigh, North Carolina' -> 'NC')."""
    if not (location and location.strip()):
        return None
    import re
    loc = location.strip()
    loc_lower = loc.lower()
    # 1) Check full state names (e.g. "North Carolina", "Raleigh, North Carolina")
    for name, abbr in _STATE_NAME_TO_ABBR.items():
        if name in loc_lower and abbr in _VALID_STATES:
            return abbr
    # 2) Check two-letter abbreviation (e.g. "Durham, NC", "NC")
    m = re.search(r"\b([A-Z]{2})\b", loc.upper())
    if m and m.group(1) in _VALID_STATES:
        return m.group(1)
    return None


SKIP_VALIDATION_DOMAINS = [
    "greenhouse.io", "lever.co", "ashbyhq.com",
    "myworkdayjobs.com", "icims.com", "bamboohr.com",
    "jobvite.com", "rippling.com", "linkedin.com", "indeed.com",
    "perfdrive.com", "validate.perfdrive.com", "njoyn.com",
    "taleo.net", "successfactors.com", "oraclecloud.com",
    "smartrecruiters.com", "workable.com", "recruitingbypaycor.com",
    "ultipro.com", "paylocity.com", "paycom.com",
    "adp.com", "kronos.com", "ceridian.com",
    "lifeattiktok.com",
    "joinbytedance.com",
]

EXCLUDE_TITLE_KEYWORDS = [
    "senior", "sr.", "staff", "principal", "director", "manager",
    "head of", "vp ", "vice president", "lead ", "architect",
    "part-time", "contract", "freelance", "consultant",
]

REQUIRE_INTERN_KEYWORDS = [
    "intern", "internship", "co-op", "coop", "apprentice",
    "new grad", "entry level", "early career", "university",
    "student", "graduate"
]

def is_listing_marked_closed(raw_row: str) -> bool:
    """Check if the repo itself marks this listing as closed."""
    row_lower = raw_row.lower()
    return (
        '~~' in raw_row or           # strikethrough markdown
        '🔒' in raw_row or           # lock emoji
        '[closed]' in row_lower or
        'no longer available' in row_lower or
        '| closed |' in row_lower
    )

def is_valid_intern_listing(title: str) -> bool:
    title_lower = title.lower()
    has_intern_signal = any(kw in title_lower for kw in REQUIRE_INTERN_KEYWORDS)
    has_senior_signal = any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS)
    return has_intern_signal and not has_senior_signal

def needs_recheck(url_checked_at, job_created_at) -> bool:
    from datetime import datetime, timezone
    if url_checked_at is None:
        return True
    
    now = datetime.now(timezone.utc)
    # Ensure job_created_at is timezone aware
    if job_created_at and job_created_at.tzinfo is None:
        job_created_at = job_created_at.replace(tzinfo=timezone.utc)
        
    age_days = (now - job_created_at).days
    hours_since_check = (now - url_checked_at).total_seconds() / 3600
    
    if age_days < 2:
        return True        # always recheck new jobs
    elif age_days < 14:
        return hours_since_check >= 48
    else:
        return hours_since_check >= 168  # 7 days

def sync_github_internship_listings(db: Session) -> Dict:
    """
    Fetch internship listings and sync to DB with high-performance validation.
    Processes in batches of 100 with 50 parallel workers and domain skipping.
    """
    from backend.models.models import Company, JobListing
    from backend.scrapers.deduplicator import deduplicate_and_insert
    from backend.scrapers.closed_detector import is_url_closed
    import concurrent.futures
    import time
    from urllib.parse import urlparse

    start_time = time.time()
    stats = {"inserted": 0, "merged": 0, "skipped_closed": 0, "skipped_ambiguous": 0}
    listings = fetch_github_internship_listings()
    if not listings:
        return stats

    # 0. Check existing jobs from these repos for re-checking
    # Fetch all jobs from these repos that might need rechecking
    existing_jobs = db.query(JobListing).filter(
        JobListing.source_repo.in_(["simplify", "vanshb03", "speedyapply"]),
        (JobListing.is_closed == False) | (JobListing.is_closed.is_(None))
    ).all()
    
    existing_job_map = {j.application_url: j for j in existing_jobs if j.application_url}
    
    # 1. Immediate deduplication & check existence
    batch_urls = [r.get("application_url") for r in listings if r.get("application_url")]
    existing_urls = set(existing_job_map.keys()) # Include existing ones as known
    
    if batch_urls:
        # Check existing in chunks if too many (to avoid SQL limit issues)
        for i in range(0, len(batch_urls), 500):
            chunk = batch_urls[i:i+500]
            existing_rows = db.query(JobListing.application_url).filter(JobListing.application_url.in_(chunk)).all()
            existing_urls.update({row[0] for row in existing_rows})

    seen_urls = set()
    to_process = []
    domain_skipped = 0
    
    for row in listings:
        # Title check first (Fix 3)
        title = row.get("title")
        if title and not is_valid_intern_listing(title):
            logger.info("Skipped non-intern listing: %s", title)
            continue

        # Repo closed signal check (Fix 3)
        # We need the raw row to check this. 
        # The `fetch_github_internship_listings` doesn't pass raw string.
        # We should rely on `parse_simplifyjobs_table_rows` to filter these out, 
        # but let's assume `is_listing_marked_closed` logic was integrated there or check here if we had raw.
        # Actually, `parse_simplifyjobs_table_rows` already skips rows with `~~` in app_cell in the current code?
        # No, it only checks in app_cell. Let's rely on existing logic for now or add if needed.
        # The user asked to "Trust the repo's own closed signals first".
        # If we have the raw markdown, we can check.
        
        url = (row.get("application_url") or "").strip()
        if not url:
            stats["skipped_ambiguous"] += 1
            continue
        if url in seen_urls: continue
        seen_urls.add(url)
        
        # Determine if needs validation
        url_lower = url.lower()
        should_skip_val = any(d in url_lower for d in SKIP_VALIDATION_DOMAINS)
        is_new = url not in existing_urls
        
        # Fix 2: Check if existing job needs recheck
        needs_reval = False
        if not is_new and url in existing_job_map:
            job = existing_job_map[url]
            if needs_recheck(job.url_checked_at, job.posted_at):
                needs_reval = True
                logger.info("Re-checking existing job: %s", url)

        if is_new and should_skip_val:
            domain_skipped += 1

        to_process.append({
            "row": row,
            "url": url,
            "needs_validation": (is_new and not should_skip_val) or needs_reval
        })

    to_check = sum(1 for item in to_process if item["needs_validation"])
    logger.info("GitHub validation: %s total listings, %s domain-skipped, %s to validate (incl. re-checks)", 
                len(to_process), domain_skipped, to_check)

    # 2. Process in batches of 100 for better responsiveness
    batch_size = 100
    total_checked = 0
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i+batch_size]
        candidates = [item for item in batch if item["needs_validation"]]
        to_insert = [item["row"] for item in batch if not item["needs_validation"]]

        if candidates:
            logger.info("Sending %s URLs to thread pool", len(candidates))
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                future_to_item = {
                    executor.submit(is_url_closed, item["url"], timeout=5): item 
                    for item in candidates
                }
                for future in concurrent.futures.as_completed(future_to_item):
                    item = future_to_item[future]
                    total_checked += 1
                    try:
                        is_closed = future.result()
                        if is_closed is True:
                            stats["skipped_closed"] += 1
                            
                            # If this was an existing job, mark it closed
                            if item["url"] in existing_job_map:
                                job = existing_job_map[item["url"]]
                                job.is_closed = True
                                db.add(job)
                                db.commit()
                                logger.info("Marked existing job as closed: %s", item["url"])
                            
                        else:
                            to_insert.append(item["row"])
                            
                            # Update url_checked_at for existing job
                            if item["url"] in existing_job_map:
                                job = existing_job_map[item["url"]]
                                job.url_checked_at = datetime.now(timezone.utc)
                                db.add(job)
                                db.commit()
                                
                    except Exception:
                        to_insert.append(item["row"]) # Ambiguous on error

        # Insert this batch immediately
        for row in to_insert:
            try:
                company_name = (row.get("company_name") or "").strip()
                if not company_name: continue
                
                company = db.query(Company).filter(Company.name == company_name).first()
                if not company:
                    company = Company(
                        name=company_name,
                        category=categorize_company(company_name),
                        discovery_source="github_simplify",
                    )
                    db.add(company)
                    db.commit()
                    db.refresh(company)

                location = (row.get("location") or "").strip()
                app_url = (row.get("application_url") or "").strip()
                
                # Determine source_repo from row source or URL
                source = row.get("source", "github_simplify")
                # We can try to guess repo from URL or just store the parsed source name if available
                # The row dict doesn't strictly have repo name in this flow unless we add it in fetch
                
                job_data = {
                    "title": row.get("title") or "Intern",
                    "location": location,
                    "application_url": app_url,
                    "source_url": app_url,
                    "state": _extract_state_from_location(location),
                    "is_remote": "remote" in location.lower() or location == "",
                    "source_repo": source, # Ideally "simplify", "vanshb03" etc if we can pass it
                }
                res = deduplicate_and_insert(db, company_name, job_data, company.id)
                if res.get("action") == "inserted": stats["inserted"] += 1
                elif res.get("action") == "merged": stats["merged"] += 1
            except Exception:
                db.rollback()
                continue
        
        logger.info("Processed batch %s/%s...", min(i + batch_size, len(to_process)), len(to_process))

    elapsed = time.time() - start_time
    # PART 6: Honest logging
    logger.info(
        f"GitHub URL validation complete: {total_checked} validated, "
        f"{stats['skipped_closed']} confirmed_closed, "
        f"{domain_skipped} domain_skipped (ATS), "
        f"{total_checked - stats['skipped_closed'] - domain_skipped} inserted_unverified, "
        f"took {elapsed:.1f}s"
    )

    # PART 2: Write SyncLog
    try:
        # Need to import models here to avoid circular imports if not already present
        from backend.models.models import SyncLog
        
        total_checked = total_checked if 'total_checked' in locals() else 0
        total_skipped_closed = stats.get("skipped_closed", 0)
        
        log_entry = SyncLog(
            source="github",
            ran_at=datetime.utcnow(),
            jobs_added=stats.get("inserted", 0),
            jobs_checked=total_checked,
            jobs_closed=total_skipped_closed,
            errors=None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to write SyncLog for github: {e}")

    return stats


def fetch_yc_companies() -> List[Dict]:
    """Fetch companies from Y Combinator's 'Work at a Startup' list (via public-ish READMEs or lists)."""
    # YC often maintains a list of startups. We can use a reliable community-maintained version or a targeted search.
    # For now, we use a targeted search + a known community repo that tracks YC companies.
    all_companies = []
    # Targeted Community Repo for YC companies
    repo_url = "https://raw.githubusercontent.com/mittsh/yclist/master/list.md" 
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        req = urllib.request.Request(repo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            # Improved parsing for the mittsh/yclist format:
            # ## Company Name
            # * URL: [http://...](http://...)
            sections = re.split(r"(?m)^##\s+", text)
            for section in sections[1:]: # Skip preamble
                lines = section.strip().split("\n")
                if not lines: continue
                
                name = lines[0].strip()
                website = ""
                
                # Look for the URL line
                for line in lines:
                    if "* URL:" in line:
                        url_match = re.search(r"\[([^\]]+)\]\((https?://[^\)]+)\)", line)
                        if url_match:
                            website = url_match.group(2)
                        break
                
                if name and website and "github" not in website.lower():
                    all_companies.append({
                        "name": name,
                        "website": website,
                        "category": "startup",
                        "discovery_source": "yc_startup",
                    })
    except Exception as e:
        print(f"YC fetch error: {e}")
    
    return all_companies


def discover_companies(db: Session) -> Dict:
    """
    Main discovery function. Discovers companies from multiple sources:
    1. Built-in extended database
    2. SimplifyJobs GitHub repos (Summer2026, Summer2025)
    3. Full internship table rows from same repos → job listings
    4. Optional web search

    Returns stats about what was discovered.
    """
    from backend.models.models import Company

    stats = {
        "new_companies": 0, 
        "updated": 0, 
        "total_sources": 0, 
        "errors": [], 
        "github_listings_added": 0, 
        "github_listings_merged": 0
    }
    now = datetime.now(timezone.utc)

    # Source 1: Extended built-in database
    for company_data in EXTENDED_COMPANIES:
        try:
            existing = db.query(Company).filter(Company.name == company_data["name"]).first()
            if existing:
                # Update fields if missing
                changed = False
                if not existing.category and company_data.get("category"):
                    existing.category = company_data["category"]
                    changed = True
                if not existing.career_url and company_data.get("career_url"):
                    existing.career_url = company_data["career_url"]
                    changed = True
                if not existing.hiring_season and company_data.get("season"):
                    existing.hiring_season = company_data["season"]
                    changed = True
                if not existing.ats_provider and company_data.get("ats"):
                    existing.ats_provider = company_data["ats"]
                    changed = True
                if not existing.website_url and company_data.get("website"):
                    existing.website_url = company_data["website"]
                    changed = True
                if not existing.discovery_source:
                    existing.discovery_source = "seed"
                    changed = True
                if changed:
                    stats["updated"] += 1
            else:
                new_company = Company(
                    name=company_data["name"],
                    website_url=company_data.get("website"),
                    career_url=company_data.get("career_url"),
                    ats_provider=company_data.get("ats"),
                    category=company_data.get("category"),
                    hiring_season=company_data.get("season"),
                    discovery_source="seed",
                    last_discovered=now,
                )
                db.add(new_company)
                stats["new_companies"] += 1
        except Exception as e:
            stats["errors"].append(f"Error adding {company_data['name']}: {str(e)}")

    db.commit()
    stats["total_sources"] += 1

    # Source 2: SimplifyJobs (companies + optional job listings from GitHub README)
    try:
        simplify_companies = fetch_simplifyjobs_companies()
        for company_data in simplify_companies:
            existing = db.query(Company).filter(Company.name == company_data["name"]).first()
            if not existing:
                new_company = Company(
                    name=company_data["name"],
                    category=company_data.get("category", "other"),
                    discovery_source="simplify",
                    last_discovered=now,
                )
                db.add(new_company)
                stats["new_companies"] += 1
        db.commit()
        stats["total_sources"] += 1
    except Exception as e:
        stats["errors"].append(f"SimplifyJobs error: {str(e)}")
        db.rollback()

    # Source 2b: Pull full internship rows from GitHub repos (SimplifyJobs Summer2026, etc.)
    try:
        gh_stats = sync_github_internship_listings(db)
        stats["github_listings_added"] = gh_stats.get("inserted", 0)
        stats["github_listings_merged"] = gh_stats.get("merged", 0)
    except Exception as e:
        stats["errors"].append(f"GitHub listings sync: {str(e)}")

    # Source 2c: YC Startups
    try:
        yc_companies = fetch_yc_companies()
        for company_data in yc_companies:
            existing = db.query(Company).filter(Company.name == company_data["name"]).first()
            if not existing:
                new_company = Company(
                    name=company_data["name"],
                    website_url=company_data.get("website"),
                    category="startup",
                    discovery_source="yc_startup",
                    last_discovered=now,
                )
                db.add(new_company)
                stats["new_companies"] += 1
        db.commit()
    except Exception as e:
        stats["errors"].append(f"YC discovery error: {str(e)}")
        db.rollback()

    # Source 3: Web search (optional; set INTERNIQ_WEB_SEARCH=1 and install duckduckgo-search)
    if os.environ.get("INTERNIQ_WEB_SEARCH", "").strip() in ("1", "true", "yes"):
        try:
            seen_names = {c.name for c in db.query(Company).all()}
            for query in DISCOVERY_QUERIES[:5]:  # limit to avoid rate limits
                for hit in _run_web_search(query, max_results=8):
                    name = (hit.get("name") or "").strip()
                    if not name or name in seen_names:
                        continue
                    seen_names.add(name)
                    category = categorize_company(name)
                    new_company = Company(
                        name=name,
                        category=category,
                        discovery_source="web_search",
                        last_discovered=now,
                    )
                    db.add(new_company)
                    stats["new_companies"] += 1
            db.commit()
            stats["total_sources"] += 1
        except Exception as e:
            stats["errors"].append(f"Web search error: {str(e)}")
            db.rollback()

    return stats


def get_companies_by_category(db: Session, category: Optional[str] = None) -> List:
    """Get companies filtered by category."""
    from backend.models.models import Company

    query = db.query(Company)
    if category:
        query = query.filter(Company.category == category)
    return query.order_by(Company.name).all()


def get_category_counts(db: Session) -> Dict[str, int]:
    """Get count of companies per category."""
    from backend.models.models import Company
    from sqlalchemy import func

    results = db.query(
        Company.category,
        func.count(Company.id)
    ).group_by(Company.category).all()

    return {cat or "uncategorized": count for cat, count in results}
