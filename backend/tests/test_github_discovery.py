"""
Direct test of company discovery + GitHub internship listings (no server needed).
Run from project root: python backend/test_github_discovery.py
"""
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    from backend.models.database import SessionLocal
    from backend.scrapers.company_discovery import (
        fetch_github_internship_listings,
        fetch_simplifyjobs_companies,
        sync_github_internship_listings,
        discover_companies,
    )

    print("InternIQ discovery test (GitHub repos + DB sync)\n")

    # 1. Fetch companies from GitHub (no DB)
    print("--- Fetch companies from SimplifyJobs README ---")
    companies = fetch_simplifyjobs_companies()
    print(f"  Companies parsed: {len(companies)}")
    if companies:
        print(f"  Sample: {companies[0]['name']} ({companies[0].get('category', '')})")

    # 2. Fetch full table rows (listings) from GitHub
    print("\n--- Fetch internship table rows from GitHub ---")
    listings = fetch_github_internship_listings()
    print(f"  Listings parsed: {len(listings)}")
    if listings:
        row = listings[0]
        print(f"  Sample: {row.get('company_name')} | {row.get('title')} | {row.get('location')}")
        print(f"  Apply URL: {(row.get('application_url') or '')[:60]}...")

    # 3. DB sync (requires DB)
    print("\n--- Sync to database ---")
    from backend.real_seed import init_db
    init_db()
    db = SessionLocal()
    try:
        result = discover_companies(db)
        print(f"  new_companies: {result.get('new_companies', 0)}")
        print(f"  updated: {result.get('updated', 0)}")
        print(f"  github_listings_added: {result.get('github_listings_added', 0)}")
        print(f"  github_listings_merged: {result.get('github_listings_merged', 0)}")
        if result.get("errors"):
            print(f"  errors: {result['errors']}")
    finally:
        db.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
