from sqlalchemy.orm import Session
from backend.models.database import engine, Base, SessionLocal
from backend.models.models import User, Company, JobListing, Application, SearchLog
import logging

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized (fresh).")

def populate_mock_data():
    db = SessionLocal()
    if db.query(User).first():
        logging.info("Data already exists. Skipping population.")
        db.close()
        return

    # === Users ===
    test_user = User(
        email="test@student.edu", full_name="Alice Student",
        graduation_year=2026, skills="Python, React, SQL, Java, Node.js",
        location="CA"
    )
    db.add(test_user)

    # === Companies ===
    companies = [
        Company(name="TechCorp", website_url="https://techcorp.com", ats_provider="Lever"),
        Company(name="DataStartup", website_url="https://datastartup.io", ats_provider="Greenhouse"),
        Company(name="WebSolutions", website_url="https://websolutions.dev", ats_provider="Workday"),
        Company(name="CloudBase", website_url="https://cloudbase.io", ats_provider="Lever"),
        Company(name="FinTech Labs", website_url="https://fintechlabs.com", ats_provider="Greenhouse"),
        Company(name="AIVentures", website_url="https://aiventures.ai", ats_provider="Lever"),
        Company(name="CyberShield", website_url="https://cybershield.com", ats_provider="Workday"),
        Company(name="GreenEnergy Tech", website_url="https://greenenergy.tech", ats_provider="Lever"),
        Company(name="HealthCode", website_url="https://healthcode.io", ats_provider="Greenhouse"),
        Company(name="GameForge Studios", website_url="https://gameforge.gg", ats_provider="Lever"),
        Company(name="RoboLogic", website_url="https://robologic.ai", ats_provider="Workday"),
        Company(name="MediaStack", website_url="https://mediastack.com", ats_provider="Lever"),
    ]
    db.add_all(companies)
    db.commit()

    # === Job Listings ===
    jobs = [
        # California
        JobListing(title="Software Engineering Intern", description="Backend focused Python engineering. Build scalable APIs and microservices for our cloud platform.", location="San Francisco, CA", state="CA", is_remote=False, application_url="https://techcorp.com/careers/1", required_skills="Python, SQL, Docker", company_id=companies[0].id),
        JobListing(title="Machine Learning Intern", description="Work on NLP models and recommendation systems using PyTorch and TensorFlow.", location="Palo Alto, CA", state="CA", is_remote=False, application_url="https://aiventures.ai/careers/1", required_skills="Python, PyTorch, TensorFlow, ML", company_id=companies[5].id),
        JobListing(title="iOS Developer Intern", description="Build native iOS apps using Swift and SwiftUI for health monitoring.", location="San Jose, CA", state="CA", is_remote=False, application_url="https://healthcode.io/careers/1", required_skills="Swift, SwiftUI, iOS, Xcode", company_id=companies[8].id),
        
        # New York
        JobListing(title="Frontend Web Dev Intern", description="Building modern UIs with React, Next.js, and Tailwind CSS.", location="New York, NY", state="NY", is_remote=False, application_url="https://websolutions.com/apply/3", required_skills="React, Next.js, CSS, TypeScript", company_id=companies[2].id),
        JobListing(title="FinTech Backend Intern", description="Develop high-frequency trading APIs and financial data pipelines.", location="New York, NY", state="NY", is_remote=False, application_url="https://fintechlabs.com/careers/1", required_skills="Python, Java, SQL, Redis", company_id=companies[4].id),
        JobListing(title="Data Analytics Intern", description="Analyze user data and build dashboards using SQL and Tableau.", location="New York, NY", state="NY", is_remote=False, application_url="https://mediastack.com/careers/1", required_skills="SQL, Python, Tableau, Excel", company_id=companies[11].id),
        
        # Texas
        JobListing(title="DevOps Engineering Intern", description="Automate CI/CD pipelines and manage cloud infrastructure on AWS.", location="Austin, TX", state="TX", is_remote=False, application_url="https://cloudbase.io/careers/1", required_skills="AWS, Docker, Kubernetes, Terraform", company_id=companies[3].id),
        JobListing(title="Game Developer Intern", description="Build multiplayer game systems using Unity and C#.", location="Austin, TX", state="TX", is_remote=False, application_url="https://gameforge.gg/careers/1", required_skills="Unity, C#, Networking, Game Design", company_id=companies[9].id),
        
        # Washington
        JobListing(title="Cloud Infrastructure Intern", description="Design and build cloud-native applications on Azure and GCP.", location="Seattle, WA", state="WA", is_remote=False, application_url="https://cloudbase.io/careers/2", required_skills="Azure, GCP, Python, Go", company_id=companies[3].id),
        JobListing(title="Robotics Software Intern", description="Write motion planning and computer vision code for autonomous robots.", location="Seattle, WA", state="WA", is_remote=False, application_url="https://robologic.ai/careers/1", required_skills="Python, C++, ROS, OpenCV", company_id=companies[10].id),
        
        # Massachusetts
        JobListing(title="Cybersecurity Intern", description="Perform penetration testing and vulnerability assessments.", location="Boston, MA", state="MA", is_remote=False, application_url="https://cybershield.com/careers/1", required_skills="Python, Linux, Networking, Security", company_id=companies[6].id),
        JobListing(title="AI Research Intern", description="Conduct research on large language models and publish papers.", location="Cambridge, MA", state="MA", is_remote=False, application_url="https://aiventures.ai/careers/2", required_skills="Python, PyTorch, NLP, Research", company_id=companies[5].id),
        
        # Colorado
        JobListing(title="Backend Engineer Intern", description="Build REST APIs and microservices using Go and PostgreSQL.", location="Denver, CO", state="CO", is_remote=False, application_url="https://greenenergy.tech/careers/1", required_skills="Go, PostgreSQL, REST, gRPC", company_id=companies[7].id),
        
        # Georgia
        JobListing(title="Mobile Developer Intern", description="Build cross-platform mobile apps using Flutter and Dart.", location="Atlanta, GA", state="GA", is_remote=False, application_url="https://healthcode.io/careers/2", required_skills="Flutter, Dart, Firebase, Mobile", company_id=companies[8].id),
        
        # Illinois
        JobListing(title="Data Engineering Intern", description="Build ETL pipelines and data warehouses using Spark and Airflow.", location="Chicago, IL", state="IL", is_remote=False, application_url="https://fintechlabs.com/careers/2", required_skills="Python, Spark, Airflow, SQL", company_id=companies[4].id),
        
        # North Carolina
        JobListing(title="QA Automation Intern", description="Write automated test suites using Selenium and Cypress.", location="Raleigh, NC", state="NC", is_remote=False, application_url="https://websolutions.com/apply/4", required_skills="JavaScript, Selenium, Cypress, CI/CD", company_id=companies[2].id),
        
        # Remote
        JobListing(title="Full-Stack Developer Intern", description="Build features end-to-end using React, Node.js, and MongoDB.", location="Remote", state=None, is_remote=True, application_url="https://datastartup.com/jobs/2", required_skills="React, Node.js, MongoDB, TypeScript", company_id=companies[1].id),
        JobListing(title="Open Source Contributor Intern", description="Contribute to open source developer tools and CLI applications.", location="Remote", state=None, is_remote=True, application_url="https://techcorp.com/careers/2", required_skills="Python, Rust, Go, Git", company_id=companies[0].id),
        JobListing(title="Technical Writer Intern", description="Write API documentation, tutorials, and developer guides.", location="Remote", state=None, is_remote=True, application_url="https://cloudbase.io/careers/3", required_skills="Technical Writing, Markdown, API, Git", company_id=companies[3].id),
        JobListing(title="Product Design Intern", description="Design user interfaces and conduct usability research.", location="Remote", state=None, is_remote=True, application_url="https://mediastack.com/careers/2", required_skills="Figma, UI/UX, Prototyping, Research", company_id=companies[11].id),
        JobListing(title="Blockchain Developer Intern", description="Build smart contracts and DeFi protocols on Ethereum.", location="Remote", state=None, is_remote=True, application_url="https://fintechlabs.com/careers/3", required_skills="Solidity, Ethereum, Web3.js, JavaScript", company_id=companies[4].id),
    ]
    db.add_all(jobs)
    db.commit()

    # === Pre-seed some search logs for trending data ===
    search_seeds = [
        SearchLog(user_id=test_user.id, query="python", results_count=5),
        SearchLog(user_id=test_user.id, query="react", results_count=3),
        SearchLog(user_id=test_user.id, query="machine learning", results_count=2),
        SearchLog(user_id=test_user.id, query="frontend", results_count=4),
        SearchLog(user_id=test_user.id, query="python", results_count=5),
        SearchLog(user_id=test_user.id, query="java", results_count=2),
        SearchLog(user_id=test_user.id, query="devops", results_count=1),
        SearchLog(user_id=test_user.id, query="react", results_count=3),
        SearchLog(user_id=test_user.id, query="python", results_count=5),
        SearchLog(user_id=test_user.id, query="data science", results_count=2),
        SearchLog(user_id=test_user.id, query="cloud", results_count=3),
        SearchLog(user_id=test_user.id, query="mobile", results_count=2),
    ]
    db.add_all(search_seeds)
    db.commit()

    # === Pre-seed one application ===
    app = Application(user_id=test_user.id, job_id=jobs[0].id, status="saved", notes="Reach out to recruiter.")
    db.add(app)
    db.commit()
    
    db.close()
    logging.info("Mock data populated with 12 companies, 21 jobs, and search history.")

if __name__ == "__main__":
    init_db()
    populate_mock_data()
