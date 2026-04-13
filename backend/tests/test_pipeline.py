"""
Test the InternIQ 5-step pipeline via the API.
Run with: python backend/test_pipeline.py
Make sure the API is running first: python -m backend.main (from project root)
"""
import sys
import time

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

BASE = "http://localhost:8000"


def get(path: str):
    r = requests.get(BASE + path, timeout=30)
    r.raise_for_status()
    return r.json()


def post(path: str, **params):
    r = requests.post(BASE + path, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    print("InternIQ pipeline test (API must be running on http://localhost:8000)\n")

    # Health
    try:
        get("/health")
        print("[OK] GET /health")
    except Exception as e:
        print(f"[FAIL] Server not reachable: {e}")
        print("Start the API: from project root run  python -m backend.main")
        sys.exit(1)

    # Step 1: Discovery (includes GitHub repo pull: SimplifyJobs Summer2026, etc.)
    print("\n--- Step 1: Company discovery (+ GitHub internship listings) ---")
    r = post("/api/pipeline/discover")
    print(f"  new_companies: {r.get('new_companies', 0)}, updated: {r.get('updated', 0)}")
    print(f"  github_listings_added: {r.get('github_listings_added', 0)}, github_listings_merged: {r.get('github_listings_merged', 0)}")
    if r.get("errors"):
        print(f"  errors: {r['errors']}")

    # Step 2: Career page detection (only missing, limit 10 for speed)
    print("\n--- Step 2: Career page detection (limit=10) ---")
    r = post("/api/pipeline/detect-careers", only_missing=True, limit=10)
    print(f"  total: {r.get('total', 0)}, detected: {r.get('detected', 0)}, not_found: {r.get('not_found', 0)}")

    # Step 3: Verify positions (limit 5)
    print("\n--- Step 3: Position verification (limit=5) ---")
    r = post("/api/pipeline/verify-positions", limit=5, max_age_hours=24)
    print(f"  total_checked: {r.get('total_checked', 0)}, with_positions: {r.get('with_positions', 0)}")

    # Recheck queue & seasonal
    print("\n--- Recheck queue & seasonal ---")
    q = get("/api/pipeline/recheck-queue?limit=5")
    print(f"  recheck queue count: {q.get('count', 0)}")
    pred = get("/api/pipeline/seasonal-predictions")
    print(f"  seasonal predictions: {len(pred)} companies")

    # Status
    print("\n--- Pipeline status ---")
    s = get("/api/pipeline/status")
    for k, v in s.items():
        if k != "scraping":
            print(f"  {k}: {v}")
    if "scraping" in s:
        print(f"  scraping: {s['scraping']}")

    # Optional: run scrape (slow, set to 2 companies)
    run_scrape = "--scrape" in sys.argv
    if run_scrape:
        print("\n--- Step 4: Scrape (max_companies=2, use_ai=False) ---")
        r = post("/api/pipeline/scrape", max_companies=2, use_ai=False)
        print(f"  {r}")
    else:
        print("\n(Skip scrape by default. Run with --scrape to test Step 4.)")

    print("\nDone.")


if __name__ == "__main__":
    main()
