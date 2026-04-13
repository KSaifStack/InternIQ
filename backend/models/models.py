from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    graduation_year = Column(Integer, nullable=True)
    skills = Column(String, nullable=True)       # Comma-separated: "Python,React,SQL"
    location = Column(String, nullable=True)     # Preferred state, e.g. "CA"
    prefer_remote = Column(Boolean, default=True)

    applications = relationship("Application", back_populates="user")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    website_url = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)  # FAANG, startup, etc.

    jobs = relationship("JobListing", back_populates="company")


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    state = Column(String, nullable=True, index=True)   # US state abbreviation
    is_remote = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_2026 = Column(Boolean, default=True)             # Only 2026 roles
    application_url = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    required_skills = Column(String, nullable=True)     # Comma-separated
    tags = Column(Text, nullable=True)                  # JSON array of tags
    source = Column(String, nullable=True, index=True)  # "github_simplify", "jsearch", "remoteok"
    source_url = Column(String, nullable=True)          # Origin URL / repo URL
    listing_hash = Column(String, nullable=True, index=True)  # MD5 fingerprint for dedup
    company_id = Column(Integer, ForeignKey("companies.id"))
    posted_at = Column(DateTime(timezone=True), nullable=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("job_listings.id"))
    status = Column(String, default="saved")    # saved, applied, interviewing, offered, rejected
    notes = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="applications")
    job = relationship("JobListing", back_populates="applications")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(String, index=True)
    state_filter = Column(String, nullable=True)
    remote_filter = Column(Boolean, default=False)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)   # "github_simplify", "remoteok", "jsearch", etc.
    ran_at = Column(DateTime(timezone=True), server_default=func.now())
    jobs_added = Column(Integer, default=0)
    jobs_checked = Column(Integer, nullable=True)
    errors = Column(Text, nullable=True)
