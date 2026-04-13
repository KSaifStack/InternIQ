InternIQ
AI-Powered Internship Discovery Platform
Product Requirements Document  •  v1.0  •  2025

Document Version
1.0 — Initial Release
Status
Draft — Under Review
Target Users
Computer Science Students (Undergraduate & Graduate)
Primary Focus
Software Engineering Internships
Date
2025

1. Executive Summary
InternIQ is an AI-powered internship discovery platform purpose-built for computer science students seeking software engineering internships. Unlike existing job boards that rely on static, manually-maintained listings, InternIQ deploys an autonomous AI agent that continuously searches the web, discovers company career pages, verifies open positions, scrapes listing details, and delivers a personalized, ranked feed to each student.

The platform eliminates the need for students to juggle multiple job boards, manually track applications, or miss deadlines. InternIQ does the research, the matching, and the prep — so students can focus on applying and interviewing.

2. Problem Statement
CS students pursuing software engineering internships face a fragmented and time-consuming process:
- Internship listings are scattered across LinkedIn, Indeed, Handshake, Glassdoor, Wellfound, and hundreds of individual company career pages.
- Many listings appear on company sites days or weeks before reaching major job boards, causing students to miss early application windows.
- Students manually track applications using spreadsheets, losing track of deadlines, interview stages, and follow-ups.
- Generic job boards show irrelevant results — IT support roles, non-CS internships, and expired listings.
- There is no unified tool that combines discovery, matching, tracking, and interview prep in one place.

InternIQ solves all of these problems with a single, intelligent platform.

3. Goals & Objectives
Goal | Success Metric
--- | ---
Aggregate internship listings faster than any competitor | Listings appear within 24 hours of posting
Surface opportunities from direct company career pages | 50+ company career pages monitored at launch; 500+ within 6 months
Personalize results to each student's profile | Match score accuracy rated 4+/5 by beta users
Reduce time spent searching for internships | Students find relevant listings 60% faster vs. baseline
Cover letter & resume tools save student time | 90% of users generate at least one AI document per session

4. Target Users

4.1 Primary Users
- Undergraduate CS students (freshmen through seniors) at US universities
- Graduate CS students (MS, PhD) seeking industry internships
- Students specializing in: Software Engineering, Backend, Frontend, Full-Stack, ML/AI, Data Science, Mobile, DevOps

4.2 User Personas
- **The Junior Seeker**: Sophomore with limited experience. Needs guidance on where to start, what skills matter, and which companies recruit early-career talent.
- **The Returning Intern**: Junior who interned before and wants to upgrade — targeting FAANG or high-growth startups with better pay and prestige.
- **The International Student**: Needs visa sponsorship filtering. Worried about OPT/CPT eligibility. Wants to avoid wasting time on companies that don't sponsor.
- **The Organized Applicant**: Applies to 50+ companies. Needs robust tracking, deadline reminders, and status management to stay on top of everything.

5. Core Features

5.1 AI Agent — Autonomous Internship Discovery
The heart of InternIQ is an AI agent that runs continuously in the background, operating in a multi-step pipeline:
- **Step 1 — Company Discovery**: AI searches the web for companies known to hire CS interns. Categorizes companies automatically.
- **Step 2 — Career Page Detection**: Identifies where they post jobs and detects Applicant Tracking System (ATS).
- **Step 3 — Open Position Verification**: Verifies internship/intern keywords and checks posting dates.
- **Step 4 — Listing Scraping**: Uses Playwright (headless browser) for JavaScript-heavy pages and BeautifulSoup/Scrapy for simpler sites. Extracts core details and handles ATS platforms directly.
- **Step 5 — AI Analysis & Tagging**: Reads full job description, extracts structured data using Claude/GPT-4 API, tags listings with skills, filters false positives, and normalizes job titles.

5.2 Student Profile & Personalization
- Onboarding quiz: graduation year, GPA, skills, interests, preferences.
- Resume upload: AI parses resume to auto-populate skills and experience.
- Each listing receives a match score (0–100%) based on alignment with job requirements.
- Feed is ranked by match score by default.

5.3 Multi-Source Aggregation
InternIQ pulls from multiple sources simultaneously: Greenhouse, Lever, Workday, LinkedIn, Handshake, Indeed, Wellfound, Glassdoor, and Direct company career pages.

5.4 Application Tracker
- Students log where they've applied with one click.
- Status tracking, deadline countdown timers, notes field, and dashboard overview.

5.5 AI Career Assistant
- Resume Reviewer, Cover Letter Generator, Cold Email Writer, Interview Prep, Skill Gap Analysis.

5.6 Insights Dashboard
- Live trend dashboard, skill demand tracker, salary intelligence, application season calendar.

6. Technical Architecture
- **AI Agent Orchestration**: LangChain
- **NLP**: Claude API / OpenAI GPT-4
- **Semantic Job Matching**: Vector embeddings via Pinecone or Weaviate
- **Web Scraping**: BeautifulSoup + Scrapy, Playwright
- **Web Search**: Google Search API or Perplexity API
- **Job Scheduling**: Celery + Redis
- **Database**: PostgreSQL + MongoDB
- **Backend API**: FastAPI (Python) or Node.js/Express
- **Frontend**: React + Tailwind CSS
- **Authentication**: OAuth 2.0 (Google, GitHub login)
- **Proxy Management**: Rotating residential proxies
- **Hosting**: AWS or GCP (containerized via Docker + Kubernetes)

7. MVP Scope & Roadmap

**Phase 1 — MVP (Months 1–3)**
- Seed database with 50 known CS employers
- Build Greenhouse + Lever API integrations
- Build Playwright scraper for Workday
- Basic student profile (skills, graduation year, location)
- Listing feed with keyword search and basic filters
- Manual application tracker (saved / applied / rejected)

**Phase 2 — AI Layer (Months 4–6)**
...
**Phase 3 — Scale & Intelligence (Months 7–12)**
...

8. Non-Functional Requirements
- Listing freshness: <24 hours
- Scraping reliability: 99%+ uptime
- Search performance: <2s load
- Data accuracy: <5% false positives
- Scalability: 100,000+ users Year 1
- Legal compliance, Data privacy, Availability SLA 99.9%

9. Risks & Mitigations
- LinkedIn blocks scrapers, ToS violations, AI hallucinations, Career page structure changes, Privacy breaches, Competitive response.

10. Success Metrics
- Acquisition, Engagement, Outcome.

11. Glossary
- ATS, AI Agent, Match Score, Semantic Matching, Vector Embeddings, Playwright, OPT/CPT
