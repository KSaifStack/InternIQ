"""
GitHub 2026 Internship Repo Syncer
Clones / pulls the five active 2026 repos and parses their README markdown tables.
"""
import subprocess
import re
import html as html_lib
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def clean_description(raw: str) -> str:
    """Strip markdown artifacts and raw HTML from job descriptions before storage."""
    if not raw:
        return ""
    # Decode HTML entities (&amp; &lt; etc.)
    cleaned = html_lib.unescape(raw)
    # Convert markdown links [text](url) → text
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Strip bold/italic markers ***text***, **text**, *text*
    cleaned = re.sub(r'\*{3}(.+?)\*{3}', r'\1', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'\*{2}(.+?)\*{2}', r'\1', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned, flags=re.DOTALL)
    # Convert markdown bullet lines (- item / * item / 1. item) → • item
    cleaned = re.sub(r'^[ \t]*[-*+][ \t]+', '• ', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^[ \t]*\d+\.[ \t]+', '• ', cleaned, flags=re.MULTILINE)
    # Replace <br/> and <br> with newline
    cleaned = re.sub(r'<br\s*/?>', '\n', cleaned, flags=re.IGNORECASE)
    # Strip remaining HTML tags (keep text content)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Collapse 3+ blank lines → 2
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

# ── 2026 Repos ────────────────────────────────────────────────────────────────

REPOS: Dict[str, Dict] = {
    "github_simplify_interns": {
        "url": "https://github.com/SimplifyJobs/Summer2026-Internships.git",
        "label": "SimplifyJobs/Summer2026-Internships",
    },
    "github_speedyapply_swe": {
        "url": "https://github.com/speedyapply/2026-SWE-College-Jobs.git",
        "label": "speedyapply/2026-SWE-College-Jobs",
    },
    "github_vanshb_interns": {
        "url": "https://github.com/vanshb03/Summer2026-Internships.git",
        "label": "vanshb03/Summer2026-Internships",
    },
    "github_speedyapply_ai": {
        "url": "https://github.com/speedyapply/2026-AI-College-Jobs.git",
        "label": "speedyapply/2026-AI-College-Jobs",
    },
    # SimplifyJobs/New-Grad-2026 removed — repo does not exist (returns 404)
}

import io
import zipfile
import httpx

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "repos"

def _sync_repo_readme(name: str, url: str) -> Optional[str]:
    """Download the repo as a ZIP file to memory and return the README.md content."""
    # url: https://github.com/SimplifyJobs/Summer2026-Internships.git
    # zip: https://github.com/SimplifyJobs/Summer2026-Internships/archive/HEAD.zip
    base_url = url.replace('.git', '')
    zip_url = f"{base_url}/archive/HEAD.zip"
    
    logger.info("Downloading %s", zip_url)
    try:
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            resp = client.get(zip_url)
            resp.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                # Find the README file
                for info in z.infolist():
                    if info.filename.lower().endswith('readme.md'):
                        return z.read(info.filename).decode('utf-8', errors='replace')
                        
        logger.warning("No README.md found in %s", name)
        return None
    except Exception as e:
        logger.error("Failed to download zip for %s: %s", name, e)
        return None

def _extract_url_from_cell(cell: str) -> str:
    """Pull href from markdown link like [Apply](url) or return raw text."""
    match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', cell)
    if match:
        return match.group(1).strip()
    # Sometimes it's just a bare URL
    bare = re.search(r'https?://\S+', cell)
    return bare.group(0).strip() if bare else ""


def _extract_state(location: str) -> str:
    state_map = {
        "california": "CA", "new york": "NY", "texas": "TX", "washington": "WA",
        "illinois": "IL", "massachusetts": "MA", "georgia": "GA", "colorado": "CO",
        "virginia": "VA", "florida": "FL", "ohio": "OH", "michigan": "MI",
        "pennsylvania": "PA", "north carolina": "NC", "arizona": "AZ",
        "new jersey": "NJ", "minnesota": "MN", "oregon": "OR", "utah": "UT",
        "nevada": "NV", "maryland": "MD", "connecticut": "CT",
        # Abbreviations pass through
        **{abbr: abbr for abbr in [
            "CA","NY","TX","WA","IL","MA","GA","CO","VA","FL","OH","MI",
            "PA","NC","AZ","NJ","MN","OR","UT","NV","MD","CT","WI","TN",
            "MO","IN","KY","LA","AL","SC","KS","OK","IA","AR","NE","MS",
            "ID","NH","ME","RI","MT","DE","SD","ND","AK","HI","WV","WY","VT","NM"
        ]}
    }
    loc_lower = location.strip().lower()
    # Try state abbreviation at end: "New York, NY"
    parts = [p.strip() for p in loc_lower.replace(",", " ").split()]
    for p in reversed(parts):
        key = p.upper()
        if key in state_map:
            return state_map[key]
    for full, abbr in state_map.items():
        if len(full) > 2 and full in loc_lower:
            return abbr
    return ""


def parse_markdown_table(content: str, source: str) -> List[dict]:
    """
    Parse the internship markdown table from a 2026 GitHub repo README.
    Handles the canonical SimplifyJobs/speedyapply table format:
    | Company | Role | Location | Application/Link | Date Posted |
    """
    if not content:
        return []

    jobs: List[dict] = []

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # Remove empty leading/trailing
        if len(cells) < 3:
            continue

        company_raw = cells[0]
        role_raw = cells[1] if len(cells) > 1 else ""
        location_raw = cells[2] if len(cells) > 2 else ""
        link_raw = cells[3] if len(cells) > 3 else ""
        date_raw = cells[4] if len(cells) > 4 else ""

        # Skip header / separator rows
        if re.match(r'^[-\s|:]+$', line.replace("|", "")):
            continue
        company_lower = company_raw.lower()
        if "company" in company_lower or "---" in company_lower:
            continue

        # Strip markdown formatting
        company = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', company_raw).strip()
        company = re.sub(r'[*_`]', '', company).strip()
        if not company or company in ("-", "↳"):
            continue

        role = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', role_raw).strip()
        role = re.sub(r'[*_`]', '', role).strip()
        if not role:
            role = "Software Engineer Intern"

        location = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', location_raw).strip()
        location = re.sub(r'[*_`]', '', location).strip()

        app_url = _extract_url_from_cell(link_raw) or _extract_url_from_cell(company_raw)

        is_remote = "remote" in location.lower()
        state = _extract_state(location)

        # Simple date parse
        posted_at = None
        if date_raw:
            date_clean = re.sub(r'[*_`]', '', date_raw).strip()
            for fmt in ("%b %d", "%B %d", "%m/%d", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(date_clean, fmt)
                    posted_at = dt.replace(year=2026)
                    break
                except ValueError:
                    continue

        fingerprint = hashlib.md5(
            f"{company.lower()}|{role.lower()}".encode()
        ).hexdigest()

        jobs.append({
            "company": company,
            "title": role,
            "location": location,
            "state": state,
            "is_remote": is_remote,
            "application_url": app_url,
            "source": source,
            "posted_at": posted_at,
            "is_2026": True,
            "listing_hash": fingerprint,
        })

    logger.info("Parsed %d jobs from %s", len(jobs), source)
    return jobs


def sync_all_repos() -> List[dict]:
    """Download HEAD repos, extract README.md, parse jobs, and return combined list."""
    all_jobs: List[dict] = []
    for name, config in REPOS.items():
        content = _sync_repo_readme(name, config["url"])
        if not content:
            logger.warning("Skipping %s — download or read failed", name)
            continue
        jobs = parse_markdown_table(content, name)
        all_jobs.extend(jobs)
        
    logger.info("GitHub sync total: %d raw job rows", len(all_jobs))
    return all_jobs
