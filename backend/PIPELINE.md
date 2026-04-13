# InternIQ 5-Step Discovery Pipeline

## Step 1 — Company Discovery
- **Module:** `scrapers/company_discovery.py`
- **Behavior:** Builds and grows an internal database of target companies and **internship listings** without human input.
  - **Sources:** Built-in list (FAANG, mid-size tech, startup, fintech, etc.), **popular GitHub internship repos**, and optional **web search**.
  - **GitHub repos:** Pulls from [SimplifyJobs/Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships) (primary) and [Summer2025-Internships](https://github.com/SimplifyJobs/Summer2025-Internships) (fallback). Parses the README markdown tables to get **company names** and **full internship rows** (role, location, application URL). Companies are created if missing; job listings are deduplicated and inserted/merged. Response includes `github_listings_added` and `github_listings_merged`.
- **Categories:** Companies are auto-categorized (FAANG, mid_size_tech, startup, fintech, healthtech, defense, cloud_infra, cybersecurity, gaming, etc.).
- **Web search (optional):** Set `INTERNIQ_WEB_SEARCH=1` and install `duckduckgo-search`. Runs queries like "companies hiring software engineering interns 2026" and adds new companies to the DB.

**API:** `POST /api/pipeline/discover` — returns `new_companies`, `updated`, `github_listings_added`, `github_listings_merged`, `errors`.

---

## Step 2 — Career Page Detection
- **Module:** `scrapers/career_page_detector.py`
- **Behavior:** Given a company name/website, detects where they post jobs (e.g. `company.com/careers` or `boards.greenhouse.io/company`). Detects ATS: **Greenhouse, Lever, Workday, iCIMS, Taleo, SmartRecruiters**, Ashby, BambooHR, Jobvite, or custom. **Stores `career_url`** so it does not need to re-discover on subsequent runs.

**API:** `POST /api/pipeline/detect-careers` (optional: `only_missing=true`, `limit=100`)

---

## Step 3 — Open Position Verification
- **Module:** `scrapers/position_verifier.py`
- **Behavior:** Visits career pages, searches for internship/intern keywords, checks posting dates (fresh vs expired). Companies without open positions are **queued for re-check** based on `last_checked` and `max_age_hours`. **Seasonal flags:** companies that typically open in specific months (e.g. Google August, Amazon September) are tracked via `hiring_season` and `GET /api/pipeline/seasonal-predictions`.

**API:**
- `POST /api/pipeline/verify-positions` (optional: `limit=50`, `max_age_hours=24`)
- `GET /api/pipeline/recheck-queue` — list of companies queued for re-check with priority (high near hiring season)

---

## Step 4 — Listing Scraping
- **Modules:** `scrapers/ats_api.py`, `scrapers/career_page_scraper.py`, `scrapers/deduplicator.py`, `scrapers/scheduler.py`
- **Behavior:**
  - **Greenhouse / Lever:** Uses **public APIs** when `career_url` is `boards.greenhouse.io/BOARD` or `jobs.lever.co/BOARD` for structured job list; no HTML scrape needed for list.
  - **Workday / JS-heavy:** Uses **Playwright** (headless browser). Simpler sites use **BeautifulSoup** after a requests fetch; if response is too small, falls back to Playwright.
  - **Extracts:** role title, location, remote/hybrid/onsite, required skills, pay range, application link, **deadline** (regex + AI when available).
  - **Deduplication:** Same job on company site vs LinkedIn = one listing via `listing_hash` (company + title + location).

**API:** `POST /api/pipeline/scrape` (optional: `max_companies=50`, `use_ai=true`)

---

## Step 5 — AI Analysis & Tagging
- **Module:** `scrapers/ai_job_parser.py`
- **Behavior:** Reads full job description and extracts structured data. **AI provider order:** OpenAI (if `OPENAI_API_KEY`), then Anthropic/Claude (if `ANTHROPIC_API_KEY`), then Ollama. Tags include: **[Python, React, Java, ML, backend, entry-level, paid, remote, sponsorship]**, plus role (backend/frontend/full-stack) and perks.

**Env (optional):**
- `OPENAI_API_KEY` + `OPENAI_MODEL` (default `gpt-4o-mini`)
- `ANTHROPIC_API_KEY` + `ANTHROPIC_MODEL` (default `claude-3-5-haiku-20241022`)

**API:** `POST /api/pipeline/tag-jobs` — tag all untagged listings.

---

## Run Full Pipeline
- **API:** `POST /api/pipeline/run-full` (optional: `skip_scrape=false` to skip Step 4)
- **Status:** `GET /api/pipeline/status` — company counts, career pages, open positions, job counts, scraping status.
