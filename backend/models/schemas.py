from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ── User ────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: str
    graduation_year: Optional[int] = None
    skills: Optional[str] = None        # Comma-separated
    location: Optional[str] = None
    prefer_remote: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    location: Optional[str] = None
    prefer_remote: Optional[bool] = None

class User(UserBase):
    id: int
    class Config:
        from_attributes = True


# ── Company ──────────────────────────────────────────────────────────────────

class CompanyBase(BaseModel):
    name: str
    website_url: Optional[str] = None
    category: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    class Config:
        from_attributes = True


# ── JobListing ───────────────────────────────────────────────────────────────

class JobListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    state: Optional[str] = None
    is_remote: bool = False
    is_active: bool = True
    is_2026: bool = True
    application_url: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    company_id: int

class JobListingCreate(JobListingBase):
    pass

class JobListing(JobListingBase):
    id: int
    posted_at: Optional[datetime] = None
    discovered_at: Optional[datetime] = None
    company: Company

    # Rule-based relevance score (computed, not stored)
    relevance_score: Optional[int] = None

    class Config:
        from_attributes = True


# ── Application ───────────────────────────────────────────────────────────────

class ApplicationBase(BaseModel):
    job_id: int
    status: str = "saved"
    notes: Optional[str] = None
    deadline: Optional[datetime] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    deadline: Optional[datetime] = None

class Application(ApplicationBase):
    id: int
    user_id: int
    applied_at: Optional[datetime] = None
    job: JobListing
    class Config:
        from_attributes = True


# ── Insights ──────────────────────────────────────────────────────────────────

class TrendingSearch(BaseModel):
    query: str
    count: int

class TrendingSkill(BaseModel):
    skill: str
    count: int


# ── Sync ──────────────────────────────────────────────────────────────────────

class SyncResult(BaseModel):
    source: str
    jobs_added: int
    errors: Optional[str] = None
