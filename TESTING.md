# Testing the InternIQ Pipeline

## Open the website (frontend)

1. **Start the backend API** (from project root `intern_iq`):
   ```bash
   python -m backend.main
   ```
   Leave it running (listens on http://localhost:8000).

2. **Start the frontend** (new terminal, from project root):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Open in your browser:**  
   Vite will print something like `Local: http://localhost:5173/` — open that URL.  
   If it doesn’t, try **http://localhost:5173**

The site talks to the API at `http://localhost:8000` (CORS is already set for 5173–5175).

---

## 1. Start the API (backend only)

From the **project root** (`intern_iq`):

```bash
cd c:\Users\Kareem\.gemini\antigravity\scratch\intern_iq
python -m backend.main
```

Or with uvicorn:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Note:** On startup the app runs `init_db()` and `populate_real_data()`, which resets the SQLite DB and seeds it with sample companies/jobs. The DB file is `interniq.db` in the project root.

---

## 2. Run the pipeline test script

In a **second terminal**, from the project root:

```bash
python backend/test_pipeline.py
```

This will:

- Hit `GET /health`
- **Step 1:** `POST /api/pipeline/discover` (add/update companies)
- **Step 2:** `POST /api/pipeline/detect-careers` (limit 10 companies)
- **Step 3:** `POST /api/pipeline/verify-positions` (limit 5)
- `GET /api/pipeline/recheck-queue` and `GET /api/pipeline/seasonal-predictions`
- `GET /api/pipeline/status`

To also run **Step 4 (scrape)** (slower):

```bash
python backend/test_pipeline.py --scrape
```

---

## 2b. Test discovery + GitHub pull without the API server

To test **company discovery and GitHub internship listings** (SimplifyJobs Summer2026, etc.) without starting the API:

```bash
python backend/test_github_discovery.py
```

This will:

- Fetch companies and full internship rows from the GitHub README (HTML table parsing).
- Sync to the local SQLite DB (companies + job listings).
- Print `new_companies`, `github_listings_added`, `github_listings_merged`.

No server required; uses the same logic as `POST /api/pipeline/discover`.

---

## 3. Test individual endpoints (curl or browser)

Base URL: `http://localhost:8000`

| Action | Method | URL |
|--------|--------|-----|
| Health | GET | `/health` |
| Step 1 Discover | POST | `/api/pipeline/discover` |
| Step 2 Detect careers | POST | `/api/pipeline/detect-careers?only_missing=true&limit=20` |
| Step 3 Verify positions | POST | `/api/pipeline/verify-positions?limit=10&max_age_hours=24` |
| Recheck queue | GET | `/api/pipeline/recheck-queue?max_age_hours=24&limit=50` |
| Seasonal predictions | GET | `/api/pipeline/seasonal-predictions` |
| List companies | GET | `/api/pipeline/companies` |
| Categories | GET | `/api/pipeline/categories` |
| Pipeline status | GET | `/api/pipeline/status` |
| Step 4 Scrape | POST | `/api/pipeline/scrape?max_companies=5&use_ai=false` |
| Step 5 Tag jobs | POST | `/api/pipeline/tag-jobs` |
| Run full pipeline | POST | `/api/pipeline/run-full?skip_scrape=true` |

**Example (PowerShell):**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
Invoke-RestMethod -Uri "http://localhost:8000/api/pipeline/discover" -Method Post
Invoke-RestMethod -Uri "http://localhost:8000/api/pipeline/status" -Method Get
```

**Example (curl):**

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/pipeline/discover
curl http://localhost:8000/api/pipeline/status
```

---

## 4. Optional: Web search and AI

- **Web search (Step 1):** Set env and install before starting the API:
  ```bash
  set INTERNIQ_WEB_SEARCH=1
  pip install duckduckgo-search
  ```
- **Claude/GPT-4 (Step 5):** Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`; then use `use_ai=true` when calling `/api/pipeline/scrape` or run full pipeline without `skip_scrape`.

---

## 5. Swagger UI

With the API running, open:

**http://localhost:8000/docs**

You can trigger all pipeline endpoints from there.
