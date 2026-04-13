"""
Career Page Scraper - Fetches job listings from company career pages
"""
import asyncio
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Rate limiting
REQUEST_DELAY = 2  # seconds between requests


def detect_ats_provider(url: str, html: str = "") -> str:
    """
    Detect the ATS (Applicant Tracking System) provider from URL or HTML.
    """
    url_lower = url.lower()

    # Check URL patterns
    if "lever.co" in url_lower or "lever" in url_lower:
        return "Lever"
    if "greenhouse.io" in url_lower or "greenhouse" in url_lower:
        return "Greenhouse"
    if "workday.com" in url_lower or "workday" in url_lower:
        return "Workday"
    if "icims.com" in url_lower or "icims" in url_lower:
        return "iCIMS"
    if "bamboohr.com" in url_lower or "bamboo" in url_lower:
        return "BambooHR"
    if "ashbyhq.com" in url_lower or "ashby" in url_lower:
        return "Ashby"

    # Check HTML for patterns
    if html:
        html_lower = html.lower()
        if "lever.co" in html_lower or "data-lever" in html_lower:
            return "Lever"
        if "greenhouse" in html_lower:
            return "Greenhouse"
        if "workday.com" in html_lower or "workday" in html_lower:
            return "Workday"

    return "Unknown"


def extract_jobs_from_lever(html: str, base_url: str) -> List[Dict]:
    """
    Extract job listings from Lever HTML.
    """
    jobs = []
    soup = BeautifulSoup(html, "lxml")

    # Try to find job postings in Lever format
    # Lever often uses JSON embedded in the page
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and "postings" in script.string:
            try:
                import json
                # Try to find JSON data
                match = re.search(r'\{.*"postings".*\}', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    for posting in data.get("postings", []):
                        jobs.append({
                            "title": posting.get("text", ""),
                            "url": posting.get("url", ""),
                            "location": posting.get("categories", {}).get("location", ""),
                        })
            except Exception:
                pass

    # Fallback: Look for HTML elements
    if not jobs:
        job_elements = soup.select("a[href*='/jobs/']")
        for elem in job_elements:
            title = elem.get_text(strip=True)
            href = elem.get("href", "")
            if title and href:
                jobs.append({
                    "title": title,
                    "url": urljoin(base_url, href),
                    "location": "",
                })

    return jobs


def extract_jobs_from_greenhouse(html: str, base_url: str) -> List[Dict]:
    """
    Extract job listings from Greenhouse HTML.
    """
    jobs = []
    soup = BeautifulSoup(html, "lxml")

    # Greenhouse often uses JSON in scripts
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and ("jobs" in script.string or "postings" in script.string):
            try:
                import json
                # Try to find JSON data
                match = re.search(r'\{.*"jobs".*\}', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    job_list = data.get("jobs", []) or data.get("postings", [])
                    for job in job_list:
                        jobs.append({
                            "title": job.get("title", ""),
                            "url": job.get("absolute_url", ""),
                            "location": job.get("location", {}).get("name", ""),
                        })
            except Exception:
                pass

    # Fallback: Look for HTML elements
    if not jobs:
        job_elements = soup.select("a[href*='/jobs/']")
        for elem in job_elements:
            title = elem.get_text(strip=True)
            href = elem.get("href", "")
            if title and href:
                jobs.append({
                    "title": title,
                    "url": urljoin(base_url, href),
                    "location": "",
                })

    return jobs


def extract_jobs_from_workday(html: str, base_url: str) -> List[Dict]:
    """
    Extract job listings from Workday HTML.
    """
    jobs = []
    soup = BeautifulSoup(html, "lxml")

    # Workday typically requires JavaScript rendering
    # Try to find job links
    job_links = soup.select("a[href*='/jobs/']")
    for link in job_links:
        title = link.get_text(strip=True)
        href = link.get("href", "")
        if title and "job" in title.lower():
            jobs.append({
                "title": title,
                "url": urljoin(base_url, href),
                "location": "",
            })

    return jobs


async def fetch_page_with_playwright(url: str) -> Optional[str]:
    """
    Fetch a page using Playwright (for JavaScript-rendered pages).
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        print(f"Error fetching {url} with Playwright: {e}")
        return None


def fetch_page_with_requests(url: str) -> Optional[str]:
    """
    Fetch a page using requests (for simple pages).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url} with requests: {e}")
        return None


async def scrape_career_page(career_url: str, use_playwright: bool = True) -> Tuple[str, List[Dict]]:
    """
    Scrape a career page and extract job listings.

    Returns:
        Tuple of (raw_html, job_listings)
    """
    html = None
    jobs = []

    # Try requests first (faster)
    html = fetch_page_with_requests(career_url)
    # If very little content, try Playwright (JS-heavy page)
    if (not html or len(html) < 2000) and use_playwright:
        html = await fetch_page_with_playwright(career_url) or html

    # Detect ATS provider
    ats_provider = detect_ats_provider(career_url, html or "")

    # If Workday, need Playwright
    if ats_provider == "Workday" and use_playwright and (not html or len(html) < 3000):
        html = await fetch_page_with_playwright(career_url)

    if not html:
        return "", []

    # Extract jobs based on ATS provider
    if ats_provider == "Lever":
        jobs = extract_jobs_from_lever(html, career_url)
    elif ats_provider == "Greenhouse":
        jobs = extract_jobs_from_greenhouse(html, career_url)
    elif ats_provider == "Workday":
        jobs = extract_jobs_from_workday(html, career_url)
    else:
        # Generic extraction
        soup = BeautifulSoup(html, "lxml")
        job_links = soup.select("a[href]")
        for link in job_links:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if title and href and ("intern" in title.lower() or "job" in title.lower()):
                full_url = urljoin(career_url, href)
                if "/jobs/" in full_url or "/careers/" in full_url or "/job/" in full_url:
                    jobs.append({
                        "title": title,
                        "url": full_url,
                        "location": "",
                    })

    # Remove duplicates
    seen = set()
    unique_jobs = []
    for job in jobs:
        if job["url"] not in seen:
            seen.add(job["url"])
            unique_jobs.append(job)

    return html, unique_jobs


async def scrape_job_detail(job_url: str) -> Optional[str]:
    """
    Fetch a single job detail page and return its HTML.
    """
    # Try requests first
    html = fetch_page_with_requests(job_url)

    # Detect ATS and try Playwright if needed
    ats_provider = detect_ats_provider(job_url, html or "")
    if ats_provider == "Workday":
        html = await fetch_page_with_playwright(job_url)

    return html


async def get_job_listings_from_career_page(career_url: str) -> List[Dict]:
    """
    Main function to get job listings from a career page.
    Prefers Greenhouse/Lever public APIs when career_url matches; otherwise scrapes (Playwright for JS-heavy).
    Returns a list of job dicts with title, url, location (and description for Lever).
    """
    from .ats_api import get_jobs_via_ats_api
    ats_provider, api_jobs = get_jobs_via_ats_api(career_url)
    if api_jobs:
        return api_jobs
    html, jobs = await scrape_career_page(career_url)
    return jobs
