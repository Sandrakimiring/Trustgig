import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_routes import router as ai_router
app.include_router(ai_router, prefix="/ai", tags=["AI Features"])

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

app = FastAPI(
    title="TrustGig Platform API",
    description="AI-powered freelance marketplace",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # ✅ fixed — cannot use * with True
    allow_methods=["*"],
    allow_headers=["*"],
)

MATCHER_URL  = os.getenv("MATCHER_SERVICE_URL", "https://trustgig.onrender.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")


# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+254"):
        return phone
    if phone.startswith("254"):
        return f"+{phone}"
    if phone.startswith("07") or phone.startswith("01"):
        return f"+254{phone[1:]}"
    if phone.startswith("7") or phone.startswith("1"):
        return f"+254{phone}"
    return phone


def get_assigned_freelancer(job, db: Session):
    if job.assigned_freelancer_id:
        return db.query(User).filter(User.id == job.assigned_freelancer_id).first()
    top_match = (
        db.query(Match)
        .filter(Match.job_id == job.id)
        .order_by(Match.final_score.desc())
        .first()
    )
    if top_match:
        return db.query(User).filter(User.id == top_match.freelancer_id).first()
    return None


# ── Schemas ───────────────────────────────────────────────────────────────────

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
    freelancer_id: int  # ✅ who the client is hiring

class EscrowRelease(BaseModel):
    job_id: int

class MarkDone(BaseModel):
    job_id: int
    freelancer_id: int

class WorkDelivery(BaseModel):
    freelancer_id: int
    delivery_link: str
    message: str


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"service": "TrustGig Platform API", "version": "3.0.0", "status": "running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/signup", status_code=201, tags=["Auth"])
def signup(user: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    if user.role not in ("client", "freelancer"):
        raise HTTPException(status_code=400, detail="Role must be client or freelancer")
    db_user = User(
        name=user.name, phone=normalize_phone(user.phone), role=user.role,
        password_hash=hash_password(user.password),
        skills=user.skills.split(",") if user.skills else [],
        experience=user.experience, location=user.location,
        jobs_applied=user.jobs_applied or 0, jobs_completed=user.jobs_completed or 0,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Account created successfully", "id": db_user.id, "name": db_user.name, "role": db_user.role, "phone": db_user.phone}

@app.post("/login", tags=["Auth"])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    normalized = normalize_phone(credentials.phone)
    user = (
        db.query(User).filter(User.phone == normalized).first()
        or db.query(User).filter(User.phone == credentials.phone).first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Phone number not registered")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="No password set. Contact admin.")
    if user.password_hash != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    skills = user.skills if isinstance(user.skills, list) else (user.skills or "").split(",")
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
            "jobs": [{"id":j.id,"title":j.title,"budget":float(j.budget),"status":j.status,"assigned_freelancer_id":j.assigned_freelancer_id} for j in jobs]
        }
    else:
        matches = db.query(Match).filter(Match.freelancer_id == user_id).all()
        return {
            "id": user.id, "name": user.name, "role": user.role,
            "phone": user.phone, "location": user.location, "skills": user.skills,
            "jobs_completed": user.jobs_completed or 0, "jobs_applied": user.jobs_applied or 0,
            "matches": [{"job_id":m.job_id,"score":float(m.final_score),"sms_sent":m.sms_sent} for m in matches]
        }


# ── Users ─────────────────────────────────────────────────────────────────────

@app.post("/users", status_code=201, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    db_user = User(
        name=user.name, phone=normalize_phone(user.phone), role=user.role,
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


# ── Jobs ──────────────────────────────────────────────────────────────────────

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
    try:
        response = httpx.post(
            f"{MATCHER_URL}/match",
            json={"job_id": db_job.id, "skills": skills_list, "budget": float(job.budget)},
            timeout=60.0,
        )
        if response.status_code == 200:
            matches = response.json()
            for m in matches:
                db.add(Match(job_id=db_job.id, freelancer_id=m["freelancer_id"],
                             similarity_score=0.0, final_score=m["score"], sms_sent=m.get("sms_sent", False)))
            db.commit()
            for m in matches:
                freelancer = db.query(User).filter(User.id == m["freelancer_id"]).first()
                if freelancer and freelancer.phone:
                    send_match_sms(phone=freelancer.phone, job_title=db_job.title,
                                   budget=float(db_job.budget), score=m["score"], job_id=db_job.id)
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


# ── Applications ──────────────────────────────────────────────────────────────

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

##this is where I want to add rteh AI intergrations code

    # prevent duplicate applications
    existing = db.query(Match).filter(
        Match.job_id == job_id, Match.freelancer_id == payload.freelancer_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    # always create a Match row so applicant is visible to client
    match = Match(job_id=job_id, freelancer_id=payload.freelancer_id,
                  similarity_score=0.0, final_score=0.0, sms_sent=False)
    db.add(match)
    freelancer.jobs_applied = (freelancer.jobs_applied or 0) + 1
    db.commit()

    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone:
        ok = send_application_sms_to_client(
            phone=client.phone, client_name=client.name,
            freelancer_name=freelancer.name, job_title=job.title,
            job_id=job_id, score=0.0)
        print(f"[SMS] {'✅' if ok else '❌'} Application SMS → {client.name}")
    return {"message": f"{freelancer.name} applied to '{job.title}'", "job_id": job_id,
            "freelancer_id": payload.freelancer_id, "status": "pending"}

@app.get("/jobs/{job_id}/applications", tags=["Applications"])
def get_applications(job_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.job_id == job_id).all()
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
    return {"job_id": job_id, "total": len(result), "applications": result}


# ── Delivery ──────────────────────────────────────────────────────────────────

@app.post("/jobs/{job_id}/deliver", status_code=201, tags=["Delivery"])
def deliver_work(job_id: int, payload: WorkDelivery, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    # upsert — allow resubmission after rejection
    delivery = db.query(Delivery).filter(Delivery.job_id == job_id).first()
    if delivery:
        delivery.delivery_link = payload.delivery_link
        delivery.message = payload.message
        delivery.status = "pending"
    else:
        delivery = Delivery(
            job_id=job_id, freelancer_id=payload.freelancer_id,
            delivery_link=payload.delivery_link, message=payload.message, status="pending",
        )
        db.add(delivery)
    db.commit()
    db.refresh(delivery)

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
        send_sms(client.phone, msg)

    return {"message": "Work delivered successfully", "job_id": job_id, "delivery_id": delivery.id, "status": "pending"}

@app.get("/jobs/{job_id}/delivery", tags=["Delivery"])
def get_delivery(job_id: int, db: Session = Depends(get_db)):
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
    delivery = db.query(Delivery).filter(Delivery.job_id == job_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery found")
    if delivery.status == "approved":
        raise HTTPException(status_code=400, detail="Already approved — payment already released")
    delivery.status = "approved"
    job = db.query(Job).filter(Job.id == job_id).first()
    if job.status == "completed":
        raise HTTPException(status_code=400, detail="Job already completed")
    job.status = "completed"
    db.commit()

    freelancer = get_assigned_freelancer(job, db)
    if freelancer and freelancer.phone:
        send_mpesa_disbursement(phone=freelancer.phone, name=freelancer.name,
                                amount=float(job.budget), job_title=job.title)
        send_payment_released_sms(phone=freelancer.phone, name=freelancer.name,
                                  amount=float(job.budget), job_title=job.title)
        freelancer.jobs_completed = (freelancer.jobs_completed or 0) + 1
        db.commit()

    return {"message": "Delivery approved and payment released", "job_id": job_id}

@app.post("/jobs/{job_id}/reject", tags=["Delivery"])
def reject_delivery(job_id: int, db: Session = Depends(get_db)):
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
    return {"message": "Delivery rejected — freelancer notified", "job_id": job_id}


# ── Matching ──────────────────────────────────────────────────────────────────

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


# ── Escrow & Payments ─────────────────────────────────────────────────────────

@app.post("/escrow/fund", status_code=201, tags=["Escrow"])
def fund_escrow(payload: EscrowFund, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail=f"Job is already '{job.status}'")
    freelancer = db.query(User).filter(User.id == payload.freelancer_id).first()
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")

    job.status = "in_progress"
    job.assigned_freelancer_id = payload.freelancer_id
    db.commit()

    if freelancer.phone:
        send_escrow_funded_sms(phone=freelancer.phone, freelancer_name=freelancer.name,
                               job_title=job.title, amount=payload.amount, job_id=payload.job_id)

    client = db.query(User).filter(User.id == job.client_id).first()
    if client and client.phone:
        send_sms(client.phone,
            f"Escrow Funded ✅\n"
            f"Hi {client.name},\n"
            f"KES {int(payload.amount):,} secured for '{job.title}'.\n"
            f"{freelancer.name} has been notified to begin work.")

    return {"message": "Escrow funded — freelancer notified", "job_id": payload.job_id,
            "freelancer_id": payload.freelancer_id, "amount": payload.amount, "status": "funded"}

@app.post("/escrow/release", tags=["Escrow"])
def release_payment(payload: EscrowRelease, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "completed":
        raise HTTPException(status_code=400, detail="Payment already released")
    job.status = "completed"
    db.commit()
    freelancer = get_assigned_freelancer(job, db)
    if freelancer and freelancer.phone:
        send_mpesa_disbursement(phone=freelancer.phone, name=freelancer.name,
                                amount=float(job.budget), job_title=job.title)
        send_payment_released_sms(phone=freelancer.phone, name=freelancer.name,
                                  amount=float(job.budget), job_title=job.title)
    return {"message": "Payment released", "job_id": payload.job_id, "status": "completed"}