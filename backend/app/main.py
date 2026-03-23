import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, engine, Base
from models import User, Job, Match, Delivery, MatchRequest, MatchResult
from services.sms_service import (
    send_match_sms,
    send_application_sms_to_client,
    send_escrow_funded_sms,
    send_work_done_sms_to_client,
    send_payment_released_sms,
    send_mpesa_disbursement,
    send_sms,
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

class WorkDelivery(BaseModel):
    freelancer_id: int
    delivery_link: str
    message: str


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
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    if user.role not in ("client", "freelancer"):
        raise HTTPException(status_code=400, detail="Role must be client or freelancer")
    db_user = User(
        name=user.name, phone=user.phone, role=user.role,
        password_hash=hash_password(user.password),
        skills=user.skills.split(",") if user.skills else [],
        experience=user.experience, location=user.location,
        jobs_applied=user.jobs_applied or 0, jobs_completed=user.jobs_completed or 0,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"[Auth] New {user.role} signed up: {user.name} ({user.phone})")
    return {"message": "Account created successfully", "id": db_user.id, "name": db_user.name, "role": db_user.role, "phone": db_user.phone}

@app.post("/login", tags=["Auth"])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == credentials.phone).first()
    if not user:
        raise HTTPException(status_code=401, detail="Phone number not registered")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="No password set. Contact admin.")
    if user.password_hash != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    skills = user.skills if isinstance(user.skills, list) else (user.skills or "").split(",")
    print(f"[Auth] Login: {user.name} ({user.role})")
    return {
        "message": "Login successful", "id": user.id, "name": user.name,
        "role": user.role, "phone": user.phone, "skills": skills,
        "location": user.location, "experience": user.experience,
        "jobs_completed": user.jobs_completed or 0, "jobs_applied": user.jobs_applied or 0,
    }

@app.get("/profile/{user_id}", tags=["Auth"])
def get_profile(user_id: int, db: Session = Depends(get_db)):
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
            "phone": user.phone, "location": user.location, "skills": user.skills,
            "jobs_completed": user.jobs_completed or 0, "jobs_applied": user.jobs_applied or 0,
            "matches": [{"job_id":m.job_id,"score":float(m.final_score),"sms_sent":m.sms_sent} for m in matches]
        }


# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/users", status_code=201, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
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
                db.add(Match(job_id=db_job.id, freelancer_id=m["freelancer_id"],
                             similarity_score=0.0, final_score=m["score"], sms_sent=m.get("sms_sent", False)))
            db.commit()
            for m in matches:
                freelancer = db.query(User).filter(User.id == m["freelancer_id"]).first()
                if freelancer and freelancer.phone:
                    ok = send_match_sms(phone=freelancer.phone, job_title=db_job.title,
                                        budget=float(db_job.budget), score=m["score"], job_id=db_job.id)
                    print(f"[SMS] {'✅' if ok else '❌'} → {freelancer.name}")
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
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail="Job is not open")
    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    if freelancer.role != "freelancer":
        raise HTTPException(status_code=400, detail="Only freelancers can apply")
    match = db.query(Match).filter(Match.job_id == job_id, Match.freelancer_id == payload.freelancer_id).first()
    score = float(match.final_score) if match else 0.0
    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone:
        ok = send_application_sms_to_client(
            phone=client.phone, client_name=client.name,
            freelancer_name=freelancer.name, job_title=job.title,
            job_id=job_id, score=score)
        print(f"[SMS] {'✅' if ok else '❌'} Application SMS → {client.name}")
    return {"message": f"{freelancer.name} applied to '{job.title}'", "job_id": job_id,
            "freelancer_id": payload.freelancer_id, "match_score": f"{int(score*100)}%", "status": "pending"}

@app.get("/jobs/{job_id}/applications", tags=["Applications"])
def get_applications(job_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.job_id == job_id).all()
    return {"job_id": job_id, "total": len(matches), "applications": matches}

@app.post("/jobs/{job_id}/done", tags=["Applications"])
def mark_job_done(job_id: int, payload: MarkDone, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone and freelancer:
        ok = send_work_done_sms_to_client(
            phone=client.phone, client_name=client.name,
            freelancer_name=freelancer.name, job_title=job.title,
            amount=float(job.budget), job_id=job_id)
        print(f"[SMS] {'✅' if ok else '❌'} Work done SMS → {client.name}")
    return {"message": f"Client notified — work done for job #{job_id}"}


# ══════════════════════════════════════════════════════════════════════════════
# WORK DELIVERY
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs/{job_id}/deliver", status_code=201, tags=["Delivery"])
def deliver_work(job_id: int, payload: WorkDelivery, db: Session = Depends(get_db)):
    """Freelancer submits work link + message — client gets SMS."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    delivery = Delivery(
        job_id=job_id, freelancer_id=payload.freelancer_id,
        delivery_link=payload.delivery_link, message=payload.message, status="pending",
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    print(f"[Delivery] Job #{job_id} — {freelancer.name} submitted work")

    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone:
        msg = (
            f"Work Delivered! 🎉\n"
            f"Hi {client.name},\n"
            f"{freelancer.name} delivered work for:\n"
            f"'{job.title}'\n\n"
            f"Message: {payload.message[:80]}\n\n"
            f"View: {payload.delivery_link}\n\n"
            f"Login to approve & pay:\n"
            f"{FRONTEND_URL}/index.html"
        )
        ok = send_sms(client.phone, msg)
        print(f"[SMS] {'✅' if ok else '❌'} Delivery SMS → {client.name} ({client.phone})")

    return {"message": "Work delivered successfully", "job_id": job_id, "delivery_id": delivery.id, "status": "pending"}

@app.get("/jobs/{job_id}/delivery", tags=["Delivery"])
def get_delivery(job_id: int, db: Session = Depends(get_db)):
    """Get delivery details for a job."""
    delivery = db.query(Delivery).filter(Delivery.job_id == job_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery found for this job")
    freelancer = db.query(User).filter(User.id == delivery.freelancer_id).first()
    return {
        "id": delivery.id, "job_id": delivery.job_id,
        "freelancer_id": delivery.freelancer_id,
        "freelancer_name": freelancer.name if freelancer else "Unknown",
        "delivery_link": delivery.delivery_link, "message": delivery.message,
        "status": delivery.status, "delivered_at": delivery.delivered_at,
    }

@app.post("/jobs/{job_id}/approve", tags=["Delivery"])
def approve_delivery(job_id: int, db: Session = Depends(get_db)):
    """Client approves delivery — auto releases M-Pesa payment."""
    delivery = db.query(Delivery).filter(Delivery.job_id == job_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery found")
    delivery.status = "approved"
    job = db.query(Job).filter(Job.id == job_id).first()
    job.status = "completed"
    db.commit()
    print(f"[Delivery] Job #{job_id} approved")

    top_match = db.query(Match).filter(Match.job_id == job_id).order_by(Match.final_score.desc()).first()
    if top_match:
        freelancer = db.query(User).filter(User.id == top_match.freelancer_id).first()
        if freelancer and freelancer.phone:
            send_mpesa_disbursement(phone=freelancer.phone, name=freelancer.name,
                                    amount=float(job.budget), job_title=job.title)
            send_payment_released_sms(phone=freelancer.phone, name=freelancer.name,
                                      amount=float(job.budget), job_title=job.title)
            print(f"[Payment] M-Pesa + SMS → {freelancer.name}")

    return {"message": "Delivery approved and payment released", "job_id": job_id}

@app.post("/jobs/{job_id}/reject", tags=["Delivery"])
def reject_delivery(job_id: int, db: Session = Depends(get_db)):
    """Client rejects delivery — freelancer gets SMS to revise."""
    delivery = db.query(Delivery).filter(Delivery.job_id == job_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery found")
    delivery.status = "rejected"
    db.commit()

    job = db.query(Job).filter(Job.id == job_id).first()
    freelancer = db.query(User).filter(User.id == delivery.freelancer_id).first()
    if freelancer and freelancer.phone:
        send_sms(freelancer.phone,
            f"Revision Requested 🔄\n"
            f"Hi {freelancer.name},\n"
            f"The client wants revisions for '{job.title}'.\n"
            f"Please update and resubmit.\n"
            f"Login: {FRONTEND_URL}/index.html")
        print(f"[SMS] Rejection SMS → {freelancer.name}")

    return {"message": "Delivery rejected — freelancer notified", "job_id": job_id}




@app.get("/match/{job_id}", tags=["Matching"])
def get_matches(job_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.job_id == job_id).all()
    if not matches:
        raise HTTPException(status_code=404, detail=f"No matches found for job_id={job_id}")
    result = []
    for m in matches:
        f = db.query(User).filter(User.id == m.freelancer_id).first()
        result.append({
            "freelancer_id": m.freelancer_id, "name": f.name if f else "Unknown",
            "phone": f.phone if f else "", "skills": f.skills if f else [],
            "score": float(m.final_score), "score_pct": f"{int(m.final_score*100)}%",
            "sms_sent": m.sms_sent,
        })
    result.sort(key=lambda x: x["score"], reverse=True)
    return {"job_id": job_id, "total_matches": len(result), "matches": result}


# ══════════════════════════════════════════════════════════════════════════════
# ESCROW & PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/escrow/fund", status_code=201, tags=["Escrow"])
def fund_escrow(payload: EscrowFund, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "in_progress"
    db.commit()
    top_match = db.query(Match).filter(Match.job_id == payload.job_id).order_by(Match.final_score.desc()).first()
    if top_match:
        freelancer = db.query(User).filter(User.id == top_match.freelancer_id).first()
        if freelancer and freelancer.phone:
            send_escrow_funded_sms(phone=freelancer.phone, freelancer_name=freelancer.name,
                                   job_title=job.title, amount=payload.amount, job_id=payload.job_id)
            print(f"[SMS] Escrow funded SMS → {freelancer.name}")
    return {"message": "Escrow funded", "job_id": payload.job_id, "amount": payload.amount, "status": "funded"}

@app.post("/escrow/release", tags=["Escrow"])
def release_payment(payload: EscrowRelease, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "completed"
    db.commit()
    top_match = db.query(Match).filter(Match.job_id == payload.job_id).order_by(Match.final_score.desc()).first()
    if top_match:
        freelancer = db.query(User).filter(User.id == top_match.freelancer_id).first()
        if freelancer and freelancer.phone:
            send_mpesa_disbursement(phone=freelancer.phone, name=freelancer.name,
                                    amount=float(job.budget), job_title=job.title)
            send_payment_released_sms(phone=freelancer.phone, name=freelancer.name,
                                      amount=float(job.budget), job_title=job.title)
            print(f"[Payment] Released → {freelancer.name}")
    return {"message": "Payment released", "job_id": payload.job_id, "status": "completed"}