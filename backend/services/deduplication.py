"""
Smart deduplication — no AI, just MD5 fingerprinting + difflib similarity.
"""
import hashlib
import re
import logging
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)

TITLE_REPLACEMENTS = {
    "swe": "software engineer",
    "software dev": "software developer",
    "software engineering": "software engineer",
    "frontend": "front end",
    "backend": "back end",
    "fullstack": "full stack",
    "full-stack": "full stack",
    "ml": "machine learning",
}

SIMILARITY_THRESHOLD = 0.85


def normalize_title(title: str) -> str:
    title = title.lower().strip()
    # Remove parentheticals like "(Summer 2026)"
    title = re.sub(r'\([^)]*\)', '', title)
    # Remove year markers
    title = re.sub(r'\b202[456]\b', '', title)
    # Remove "intern" / "internship" so "SWE Intern" == "Software Engineer Internship"
    title = re.sub(r'\bintern(ship)?\b', '', title, flags=re.IGNORECASE)
    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)
    for old, new in TITLE_REPLACEMENTS.items():
        title = title.replace(old, new)
    return re.sub(r'\s+', ' ', title).strip()


def make_fingerprint(company: str, title: str) -> str:
    """MD5 of normalized 'company|title'."""
    norm = f"{company.lower().strip()}|{normalize_title(title)}"
    return hashlib.md5(norm.encode()).hexdigest()


def is_similar(title1: str, title2: str) -> bool:
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    return SequenceMatcher(None, t1, t2).ratio() >= SIMILARITY_THRESHOLD


class JobDeduplicator:
    """In-memory fingerprint set for a single sync session."""

    def __init__(self):
        self._seen: set[str] = set()

    def is_new(self, company: str, title: str) -> bool:
        """Return True if this job hasn't been seen yet, and record it."""
        fp = make_fingerprint(company, title)
        if fp in self._seen:
            return False
        self._seen.add(fp)
        return True

    def reset(self):
        self._seen.clear()
