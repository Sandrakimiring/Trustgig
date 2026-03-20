'''This file, crud.py, contains all the database read/write operations for your system using SQLAlchemy. 🗄️💾

In short: your FastAPI routes call these functions, and no route talks to the database directly. This keeps your backend clean and organized.

Think of it as the “data access layer” of your backend.'''
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from typing import List, Optional

from app import models, schemas

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.phone == phone).first()


def get_users(db: Session, role: Optional[str] = None) -> List[models.User]:
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    return q.order_by(models.User.created_at.desc()).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_job(db: Session, job_id: int) -> Optional[models.Job]:
    return db.query(models.Job).filter(models.Job.id == job_id).first()


def get_jobs(db: Session, status: Optional[str] = None) -> List[models.Job]:
    q = db.query(models.Job)
    if status:
        q = q.filter(models.Job.status == status)
    return q.order_by(desc(models.Job.created_at)).all()


def create_job(db: Session, job: schemas.JobCreate) -> models.Job:
    db_job = models.Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job_status(db: Session, job_id: int, status: str) -> Optional[models.Job]:
    job = get_job(db, job_id)
    if job:
        job.status = status
        db.commit()
        db.refresh(job)
    return job

def get_application(db: Session, application_id: int) -> Optional[models.Application]:
    return db.query(models.Application).filter(models.Application.id == application_id).first()


def get_applications_for_job(db: Session, job_id: int) -> List[models.Application]:
    return db.query(models.Application).filter(models.Application.job_id == job_id).all()


def get_application_by_job_and_freelancer(
    db: Session, job_id: int, freelancer_id: int
) -> Optional[models.Application]:
    return db.query(models.Application).filter(
        models.Application.job_id == job_id,
        models.Application.freelancer_id == freelancer_id,
    ).first()


def create_application(
    db: Session, job_id: int, freelancer_id: int
) -> models.Application:
    app = models.Application(job_id=job_id, freelancer_id=freelancer_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_application_status(
    db: Session, application_id: int, status: str
) -> Optional[models.Application]:
    app = get_application(db, application_id)
    if app:
        app.status = status
        db.commit()
        db.refresh(app)
    return app

def get_escrow_by_job(db: Session, job_id: int) -> Optional[models.Escrow]:
    return db.query(models.Escrow).filter(models.Escrow.job_id == job_id).first()


def create_escrow(db: Session, job_id: int, amount: float) -> models.Escrow:
    escrow = models.Escrow(job_id=job_id, amount=amount, status="funded",
                           funded_at=datetime.now(timezone.utc))
    db.add(escrow)
    db.commit()
    db.refresh(escrow)
    return escrow


def release_escrow(db: Session, job_id: int) -> Optional[models.Escrow]:
    escrow = get_escrow_by_job(db, job_id)
    if escrow:
        escrow.status = "released"
        escrow.released_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(escrow)
    return escrow

def get_matches_for_job(db: Session, job_id: int) -> List[models.Match]:
    return (
        db.query(models.Match)
        .filter(models.Match.job_id == job_id)
        .order_by(desc(models.Match.score))
        .all()
    )
def save_matches(
    db: Session, job_id: int, results: List[schemas.MatchResult]
) -> List[models.Match]:
    """
    Upsert match results from Engineer B's ML service.
    If a match already exists for (job_id, freelancer_id), update the score.
    """
    saved = []
    for r in results:
        existing = db.query(models.Match).filter(
            models.Match.job_id == job_id,
            models.Match.freelancer_id == r.freelancer_id,
        ).first()

        if existing:
            existing.score = r.score
            db.commit()
            db.refresh(existing)
            saved.append(existing)
        else:
            match = models.Match(job_id=job_id, freelancer_id=r.freelancer_id, score=r.score)
            db.add(match)
            db.commit()
            db.refresh(match)
            saved.append(match)
    return saved


def mark_match_notified(db: Session, match_id: int):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if match:
        match.notified = "yes"
        db.commit()