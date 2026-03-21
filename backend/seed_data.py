import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, Job

Base.metadata.create_all(bind=engine)

FREELANCERS = [
    {"name": "Mercy Wanjiru",   "phone": "+254701000001", "role": "freelancer", "skills": "python,pandas,data analysis",       "location": "Nairobi",  "experience": "intermediate", "jobs_applied": 10, "jobs_completed": 8},
    {"name": "James Otieno",    "phone": "+254701000002", "role": "freelancer", "skills": "react,node,javascript,typescript",   "location": "Nairobi",  "experience": "expert",       "jobs_applied": 15, "jobs_completed": 13},
    {"name": "Amina Hassan",    "phone": "+254701000003", "role": "freelancer", "skills": "figma,branding,design,illustrator",  "location": "Mombasa",  "experience": "expert",       "jobs_applied": 12, "jobs_completed": 11},
    {"name": "Brian Kamau",     "phone": "+254701000004", "role": "freelancer", "skills": "django,python,postgresql,rest api",  "location": "Nairobi",  "experience": "intermediate", "jobs_applied": 8,  "jobs_completed": 6},
    {"name": "Fatuma Abdalla",  "phone": "+254701000005", "role": "freelancer", "skills": "excel,powerbi,data visualization",   "location": "Kisumu",   "experience": "intermediate", "jobs_applied": 6,  "jobs_completed": 5},
    {"name": "Kevin Mwangi",    "phone": "+254701000006", "role": "freelancer", "skills": "flutter,dart,mobile development",    "location": "Nakuru",   "experience": "beginner",     "jobs_applied": 4,  "jobs_completed": 2},
    {"name": "Grace Achieng",   "phone": "+254701000007", "role": "freelancer", "skills": "copywriting,content,seo,wordpress",  "location": "Nairobi",  "experience": "expert",       "jobs_applied": 20, "jobs_completed": 18},
    {"name": "Samuel Kipchoge", "phone": "+254701000008", "role": "freelancer", "skills": "machine learning,python,tensorflow", "location": "Eldoret",  "experience": "expert",       "jobs_applied": 7,  "jobs_completed": 7},
    {"name": "Tabitha Muthoni", "phone": "+254701000009", "role": "freelancer", "skills": "accounting,quickbooks,bookkeeping",  "location": "Thika",    "experience": "expert",       "jobs_applied": 9,  "jobs_completed": 8},
    {"name": "Daniel Omondi",   "phone": "+254701000010", "role": "freelancer", "skills": "php,laravel,mysql,wordpress",        "location": "Nairobi",  "experience": "intermediate", "jobs_applied": 5,  "jobs_completed": 4},
]

CLIENTS = [
    {"name": "TechStartup KE", "phone": "+254700000001", "role": "client", "location": "Nairobi"},
    {"name": "AgriData Ltd",   "phone": "+254700000002", "role": "client", "location": "Nakuru"},
]

SAMPLE_JOBS = [
    {
        "client_index": 0,
        "title": "Python data cleaning script",
        "description": "Clean and normalize a 10,000-row survey dataset.",
        "skills_required": "python,pandas,data analysis",
        "budget": 4000.0,
    },
    {
        "client_index": 1,
        "title": "React dashboard for farm analytics",
        "description": "Build a React dashboard showing crop yield charts.",
        "skills_required": "react,javascript",
        "budget": 15000.0,
    },
    {
        "client_index": 0,
        "title": "Logo and branding package",
        "description": "Design a logo, business card, and letterhead.",
        "skills_required": "figma,branding,design",
        "budget": 8000.0,
    },
    {
        "client_index": 1,
        "title": "Mobile app for crop disease detection",
        "description": "Flutter app that detects crop diseases from photos.",
        "skills_required": "flutter,dart,machine learning",
        "budget": 25000.0,
    },
]


def seed():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("⚠️  Database already has data. Skipping seed.")
            return

        freelancer_objs = []
        for f in FREELANCERS:
            user = User(**f)
            db.add(user)
            freelancer_objs.append(user)

        client_objs = []
        for c in CLIENTS:
            user = User(**c)
            db.add(user)
            client_objs.append(user)

        db.flush()

        for j in SAMPLE_JOBS:
            idx = j.pop("client_index")
            job = Job(client_id=client_objs[idx].id, **j)
            db.add(job)

        db.commit()
        print(f"✅ Seeded {len(FREELANCERS)} freelancers, {len(CLIENTS)} clients, {len(SAMPLE_JOBS)} jobs.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()