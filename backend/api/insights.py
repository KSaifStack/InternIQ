"""
Insights API — trending search queries and skills only. No AI.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from ..models import models, schemas, database

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/trending-searches", response_model=List[schemas.TrendingSearch])
def get_trending_searches(limit: int = 10, db: Session = Depends(database.get_db)):
    """Most popular search queries from the last 7 days."""
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    results = (
        db.query(models.SearchLog.query, func.count(models.SearchLog.id).label("count"))
        .filter(models.SearchLog.created_at >= week_ago, models.SearchLog.query != "")
        .group_by(models.SearchLog.query)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [{"query": r[0], "count": r[1]} for r in results]


@router.get("/trending-skills", response_model=List[schemas.TrendingSkill])
def get_trending_skills(limit: int = 10, db: Session = Depends(database.get_db)):
    """Count skill mentions in recent search queries and saved jobs."""
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)

    common_skills = {
        "python", "java", "javascript", "typescript", "react", "node", "sql", "aws",
        "docker", "kubernetes", "c++", "c#", "go", "rust", "html", "css", "angular",
        "vue", "django", "flask", "spring", "mongodb", "postgresql", "redis",
        "graphql", "machine learning", "ml", "ai", "data science",
        "backend", "frontend", "fullstack", "devops", "cloud",
        "mobile", "ios", "android", "flutter", "swift", "kotlin", "git", "figma",
    }

    skill_counts: dict[str, int] = {}

    # From search queries
    searches = (
        db.query(models.SearchLog.query)
        .filter(models.SearchLog.created_at >= week_ago, models.SearchLog.query != "")
        .all()
    )
    for (q,) in searches:
        for term in q.lower().split():
            if term in common_skills:
                skill_counts[term] = skill_counts.get(term, 0) + 1

    # From saved job skills
    saved = (
        db.query(models.JobListing.required_skills)
        .join(models.Application, models.Application.job_id == models.JobListing.id)
        .filter(models.JobListing.required_skills.isnot(None))
        .all()
    )
    for (skills,) in saved:
        if skills:
            for s in skills.split(","):
                s = s.strip().lower()
                if s in common_skills:
                    skill_counts[s] = skill_counts.get(s, 0) + 2  # Weight saves higher

    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"skill": s, "count": c} for s, c in sorted_skills]
