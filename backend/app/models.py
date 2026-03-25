from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    phone          = Column(String, unique=True, nullable=False)
    role           = Column(String, nullable=False)          # "client" | "freelancer"
    password_hash  = Column(String, nullable=True)
    skills         = Column(ARRAY(String), default=[])
    experience     = Column(String, nullable=True)
    location       = Column(String, nullable=True)
    jobs_applied   = Column(Integer, default=0)
    jobs_completed = Column(Integer, default=0)

    jobs    = relationship("Job",   back_populates="client")
    matches = relationship("Match", back_populates="freelancer")


class Job(Base):
    __tablename__ = "jobs"

    id                     = Column(Integer, primary_key=True, index=True)
    client_id              = Column(Integer, ForeignKey("users.id"), nullable=False)
    title                  = Column(String, nullable=False)
    description            = Column(Text, nullable=True)
    skills_required        = Column(ARRAY(String), default=[])
    budget                 = Column(Float, nullable=False)
    status                 = Column(String, default="open")   # open | in_progress | completed
    # ✅ tracks exactly who was hired — fixes escrow/release/approve guessing
    assigned_freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at             = Column(DateTime, default=datetime.utcnow)

    client             = relationship("User", foreign_keys=[client_id], back_populates="jobs")
    assigned_freelancer = relationship("User", foreign_keys=[assigned_freelancer_id])
    matches            = relationship("Match",    back_populates="job")
    deliveries         = relationship("Delivery", back_populates="job")


class Match(Base):
    __tablename__ = "matches"

    id            = Column(Integer, primary_key=True, index=True)
    job_id        = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ✅ similarity_score removed — was always 0.0 and caused the DB column error
    final_score   = Column(Float, default=0.0)
    sms_sent      = Column(Boolean, default=False)
    matched_at    = Column(DateTime, default=datetime.utcnow)

    job        = relationship("Job",  back_populates="matches")
    freelancer = relationship("User", back_populates="matches")


class Delivery(Base):
    __tablename__ = "deliveries"

    id            = Column(Integer, primary_key=True, index=True)
    job_id        = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_link = Column(String, nullable=True)
    message       = Column(Text, nullable=True)
    status        = Column(String, default="pending")   # pending | approved | rejected
    delivered_at  = Column(DateTime, default=datetime.utcnow)

    job        = relationship("Job",  back_populates="deliveries")
    freelancer = relationship("User")


# ── kept for backwards-compat if your matcher service uses these schemas ──────
class MatchRequest(Base):
    __tablename__ = "match_requests"

    id         = Column(Integer, primary_key=True, index=True)
    job_id     = Column(Integer, ForeignKey("jobs.id"))
    skills     = Column(ARRAY(String), default=[])
    budget     = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchResult(Base):
    __tablename__ = "match_results"

    id            = Column(Integer, primary_key=True, index=True)
    job_id        = Column(Integer, ForeignKey("jobs.id"))
    freelancer_id = Column(Integer, ForeignKey("users.id"))
    score         = Column(Float)
    created_at    = Column(DateTime, default=datetime.utcnow)