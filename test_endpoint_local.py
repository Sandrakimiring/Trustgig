import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trustgig.main import app
from trustgig.database import SessionLocal
from trustgig import models

client = TestClient(app)

def run_tests():
    print("Testing /health ...", flush=True)
    health_res = client.get("/health")
    print(f"Health Response: {health_res.status_code} {health_res.json()}", flush=True)

    print("\nTesting /match post ...", flush=True)
    db = SessionLocal()
    job = db.query(models.Job).first()
    
    if not job:
        print("No job in DB, creating a dummy one...")
        job = models.Job(
            client_id=1,
            title="Python scripting task",
            description="Need python script",
            skills_required=["python", "pandas"],
            budget=100.0,
            status="open"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    freelancers = db.query(models.User).filter(models.User.role == "freelancer").all()
    if not freelancers:
        print("No freelancers in DB, creating some...")
        seed = [
            models.User(name="Mercy Wanjiru",  phone="+254701000001", role="freelancer",
                        skills=["python", "pandas", "data_analysis"], jobs_applied=10, jobs_completed=8),
            models.User(name="James Otieno",   phone="+254701000002", role="freelancer",
                        skills=["react", "nodejs", "javascript"], jobs_applied=5, jobs_completed=4),
            models.User(name="Brian Kamau",    phone="+254701000004", role="freelancer",
                        skills=["django", "python", "postgresql"], jobs_applied=7, jobs_completed=6),
        ]
        db.add_all(seed)
        db.commit()
        print(f"  Seeded {len(seed)} freelancers.")

    payload = {
        "job_id": job.id,
        "skills": job.skills_required if job.skills_required else ["python"],
        "budget": float(job.budget) if job.budget else 50.0
    }
    
    match_res = client.post("/match", json=payload)
    print(f"Match Response Code: {match_res.status_code}", flush=True)
    print(f"Match Response Body: {match_res.json()}", flush=True)
    
    print("\nTesting /match/{job_id} get ...", flush=True)
    get_res = client.get(f"/match/{job.id}")
    print(f"Get Response Code: {get_res.status_code}", flush=True)
    print(f"Get Response Body: {get_res.json()}", flush=True)

if __name__ == "__main__":
    run_tests()
