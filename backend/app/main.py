import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, engine, Base
from models import User, Job, Match, MatchRequest, MatchResult
from services.sms_service import (
    send_match_sms,
    send_application_sms_to_client,
    send_escrow_funded_sms,
    send_work_done_sms_to_client,
    send_payment_released_sms,
    send_mpesa_disbursement,
)
import models

Base.metadata.create_all(bind=engine)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import httpx

# ══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="TrustGig Platform API",
    description="AI-powered freelance marketplace — Engineer A backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MATCHER_URL  = os.getenv("MATCHER_SERVICE_URL", "https://trustgig.onrender.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    name: str
    phone: str
    role: str
    skills: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None
    jobs_applied: Optional[int] = 0
    jobs_completed: Optional[int] = 0

class UserSignup(BaseModel):
    name: str
    phone: str
    password: str
    role: str
    skills: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None
    jobs_applied: Optional[int] = 0
    jobs_completed: Optional[int] = 0

class UserLogin(BaseModel):
    phone: str
    password: str

class JobCreate(BaseModel):
    client_id: int
    title: str
    description: Optional[str] = None
    skills_required: Optional[str] = None
    budget: float

class ApplicationCreate(BaseModel):
    freelancer_id: int

class EscrowFund(BaseModel):
    job_id: int
    amount: float

class EscrowRelease(BaseModel):
    job_id: int

class MarkDone(BaseModel):
    job_id: int
    freelancer_id: int


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    return {"service": "TrustGig Platform API", "version": "2.0.0", "status": "running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "TrustGig Engineer A", "port": 8000}


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/signup", status_code=201, tags=["Auth"])
def signup(user: UserSignup, db: Session = Depends(get_db)):
    """New user signs up with phone + password."""
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    if user.role not in ("client", "freelancer"):
        raise HTTPException(status_code=400, detail="Role must be client or freelancer")

    db_user = User(
        name=user.name,
        phone=user.phone,
        role=user.role,
        password_hash=hash_password(user.password),
        skills=user.skills.split(",") if user.skills else [],
        experience=user.experience,
        location=user.location,
        jobs_applied=user.jobs_applied or 0,
        jobs_completed=user.jobs_completed or 0,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"[Auth] New {user.role} signed up: {user.name} ({user.phone})")
    return {
        "message": "Account created successfully",
        "id": db_user.id,
        "name": db_user.name,
        "role": db_user.role,
        "phone": db_user.phone,
    }

@app.post("/login", tags=["Auth"])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with phone + password."""
    user = db.query(User).filter(User.phone == credentials.phone).first()
    if not user:
        raise HTTPException(status_code=401, detail="Phone number not registered")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="No password set for this account. Contact admin.")
    if user.password_hash != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    skills = user.skills if isinstance(user.skills, list) else (user.skills or "").split(",")
    print(f"[Auth] Login: {user.name} ({user.role})")
    return {
        "message": "Login successful",
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
        "skills": skills,
        "location": user.location,
        "experience": user.experience,
        "jobs_completed": user.jobs_completed or 0,
        "jobs_applied": user.jobs_applied or 0,
    }

@app.get("/profile/{user_id}", tags=["Auth"])
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Get full profile — returns jobs for clients, matches for freelancers."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "client":
        jobs = db.query(Job).filter(Job.client_id == user_id).all()
        return {
            "id": user.id, "name": user.name, "role": user.role,
            "phone": user.phone, "location": user.location,
            "jobs": [{"id":j.id,"title":j.title,"budget":float(j.budget),"status":j.status} for j in jobs]
        }
    else:
        matches = db.query(Match).filter(Match.freelancer_id == user_id).all()
        return {
            "id": user.id, "name": user.name, "role": user.role,
            "phone": user.phone, "location": user.location,
            "skills": user.skills,
            "jobs_completed": user.jobs_completed or 0,
            "jobs_applied": user.jobs_applied or 0,
            "matches": [{"job_id":m.job_id,"score":float(m.final_score),"sms_sent":m.sms_sent} for m in matches]
        }


# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/users", status_code=201, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a user without password (admin use)."""
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    db_user = User(
        name=user.name, phone=user.phone, role=user.role,
        skills=user.skills.split(",") if user.skills else [],
        experience=user.experience, location=user.location,
        jobs_applied=user.jobs_applied, jobs_completed=user.jobs_completed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"[Users] Created {user.role}: {user.name} (ID: {db_user.id})")
    return db_user

@app.get("/users", tags=["Users"])
def get_users(role: str = None, db: Session = Depends(get_db)):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.all()

@app.get("/users/{user_id}", tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ══════════════════════════════════════════════════════════════════════════════
# JOBS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs", status_code=201, tags=["Jobs"])
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """Post a job — triggers AI matching and SMS to matched freelancers."""
    client = db.query(User).filter(User.id == job.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.role != "client":
        raise HTTPException(status_code=400, detail="Only clients can post jobs")

    skills_list = [s.strip() for s in (job.skills_required or "").split(",") if s.strip()]
    db_job = Job(
        client_id=job.client_id, title=job.title, description=job.description,
        skills_required=skills_list, budget=float(job.budget), status="open",
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    print(f"\n[Jobs] New job: '{db_job.title}' (ID:{db_job.id}) by {client.name}")

    # Call ML matching service
    try:
        response = httpx.post(
            f"{MATCHER_URL}/match",
            json={"job_id": db_job.id, "skills": skills_list, "budget": float(job.budget)},
            timeout=60.0,
        )
        print(f"[Matcher] Response: {response.status_code}")
        if response.status_code == 200:
            matches = response.json()
            for m in matches:
                db.add(Match(
                    job_id=db_job.id, freelancer_id=m["freelancer_id"],
                    similarity_score=0.0, final_score=m["score"],
                    sms_sent=m.get("sms_sent", False),
                ))
            db.commit()
            print(f"[Matcher] Saved {len(matches)} matches")
            for m in matches:
                freelancer = db.query(User).filter(User.id == m["freelancer_id"]).first()
                if freelancer and freelancer.phone:
                    ok = send_match_sms(
                        phone=freelancer.phone, job_title=db_job.title,
                        budget=float(db_job.budget), score=m["score"], job_id=db_job.id,
                    )
                    print(f"[SMS] {'✅' if ok else '❌'} → {freelancer.name} ({freelancer.phone})")
    except Exception as e:
        print(f"[Matcher] Failed: {e}")

    return db_job

@app.get("/jobs", tags=["Jobs"])
def get_jobs(status: str = None, db: Session = Depends(get_db)):
    q = db.query(Job)
    if status:
        q = q.filter(Job.status == status)
    return q.all()

@app.get("/jobs/{job_id}", tags=["Jobs"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs/{job_id}/apply", status_code=201, tags=["Applications"])
def apply_to_job(job_id: int, payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Freelancer applies — client gets SMS with escrow link."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail="Job is not open for applications")

    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    if freelancer.role != "freelancer":
        raise HTTPException(status_code=400, detail="Only freelancers can apply")

    match = db.query(Match).filter(
        Match.job_id == job_id, Match.freelancer_id == payload.freelancer_id
    ).first()
    score = float(match.final_score) if match else 0.0

    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone:
        ok = send_application_sms_to_client(
            phone=client.phone, client_name=client.name,
            freelancer_name=freelancer.name, job_title=job.title,
            job_id=job_id, score=score,
        )
        print(f"[SMS] {'✅' if ok else '❌'} Application SMS → {client.name} ({client.phone})")

    return {
        "message": f"{freelancer.name} applied to '{job.title}'",
        "job_id": job_id, "freelancer_id": payload.freelancer_id,
        "match_score": f"{int(score * 100)}%", "status": "pending",
    }

@app.get("/jobs/{job_id}/applications", tags=["Applications"])
def get_applications(job_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.job_id == job_id).all()
    return {"job_id": job_id, "total": len(matches), "applications": matches}

@app.post("/jobs/{job_id}/done", tags=["Applications"])
def mark_job_done(job_id: int, payload: MarkDone, db: Session = Depends(get_db)):
    """Freelancer marks done — client gets SMS with payment release link."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone and freelancer:
        ok = send_work_done_sms_to_client(
            phone=client.phone, client_name=client.name,
            freelancer_name=freelancer.name, job_title=job.title,
            amount=float(job.budget), job_id=job_id,
        )
        print(f"[SMS] {'✅' if ok else '❌'} Work done SMS → {client.name} ({client.phone})")

    return {"message": f"Client notified — work done for job #{job_id}"}


# ══════════════════════════════════════════════════════════════════════════════
# MATCHES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/match/{job_id}", tags=["Matching"])
def get_matches(job_id: int, db: Session = Depends(get_db)):
    """Get ranked AI match results for a job."""
    matches = db.query(Match).filter(Match.job_id == job_id).all()
    if not matches:
        raise HTTPException(status_code=404, detail=f"No matches found for job_id={job_id}")
    result = []
    for m in matches:
        f = db.query(User).filter(User.id == m.freelancer_id).first()
        result.append({
            "freelancer_id": m.freelancer_id,
            "name": f.name if f else "Unknown",
            "phone": f.phone if f else "",
            "skills": f.skills if f else [],
            "score": float(m.final_score),
            "score_pct": f"{int(m.final_score * 100)}%",
            "sms_sent": m.sms_sent,
        })
    result.sort(key=lambda x: x["score"], reverse=True)
    return {"job_id": job_id, "total_matches": len(result), "matches": result}


# ══════════════════════════════════════════════════════════════════════════════
# ESCROW & PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/escrow/fund", status_code=201, tags=["Escrow"])
def fund_escrow(payload: EscrowFund, db: Session = Depends(get_db)):
    """Client funds escrow — top freelancer gets SMS to start work."""
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "in_progress"
    db.commit()
    print(f"\n[Escrow] Job #{payload.job_id} funded — KES {payload.amount}")

    top_match = (
        db.query(Match).filter(Match.job_id == payload.job_id)
        .order_by(Match.final_score.desc()).first()
    )
    if top_match:
        freelancer = db.query(User).filter(User.id == top_match.freelancer_id).first()
        if freelancer and freelancer.phone:
            ok = send_escrow_funded_sms(
                phone=freelancer.phone, freelancer_name=freelancer.name,
                job_title=job.title, amount=payload.amount, job_id=payload.job_id,
            )
            print(f"[SMS] {'✅' if ok else '❌'} Escrow funded SMS → {freelancer.name} ({freelancer.phone})")

    return {"message": "Escrow funded successfully", "job_id": payload.job_id, "amount": payload.amount, "status": "funded"}

@app.post("/escrow/release", tags=["Escrow"])
def release_payment(payload: EscrowRelease, db: Session = Depends(get_db)):
    """Client releases payment — freelancer gets M-Pesa + SMS."""
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "completed"
    db.commit()
    print(f"\n[Escrow] Payment released for job #{payload.job_id}")

    top_match = (
        db.query(Match).filter(Match.job_id == payload.job_id)
        .order_by(Match.final_score.desc()).first()
    )
    if top_match:
        freelancer = db.query(User).filter(User.id == top_match.freelancer_id).first()
        if freelancer and freelancer.phone:
            ok_mpesa = send_mpesa_disbursement(
                phone=freelancer.phone, name=freelancer.name,
                amount=float(job.budget), job_title=job.title,
            )
            print(f"[M-Pesa] {'✅' if ok_mpesa else '❌'} → {freelancer.name} ({freelancer.phone})")
            ok_sms = send_payment_released_sms(
                phone=freelancer.phone, name=freelancer.name,
                amount=float(job.budget), job_title=job.title,
            )
            print(f"[SMS] {'✅' if ok_sms else '❌'} Payment SMS → {freelancer.name} ({freelancer.phone})")

    return {"message": "Payment released successfully", "job_id": payload.job_id, "status": "completed"}