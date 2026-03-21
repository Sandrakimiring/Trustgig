from sqlalchemy import Column, Integer, String, Numeric, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from database import Base

class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String)
    phone          = Column(String)
    role           = Column(String)
    skills         = Column(JSON)
    experience     = Column(String)
    location       = Column(String)
    jobs_completed = Column(Integer, default=0)
    jobs_applied   = Column(Integer, default=0)
    last_completed = Column(DateTime, nullable=True)
    password_hash  = Column(String(200), nullable=True)   # ← NEW

class Job(Base):
    __tablename__ = "jobs"
    id              = Column(Integer, primary_key=True)
    client_id       = Column(Integer)
    title           = Column(String)
    description     = Column(String)
    skills_required = Column(JSON)
    budget          = Column(Numeric)
    status          = Column(String, default="open")

class Match(Base):
    __tablename__ = "matches"
    id               = Column(Integer, primary_key=True)
    job_id           = Column(Integer)
    freelancer_id    = Column(Integer)
    similarity_score = Column(Numeric)
    final_score      = Column(Numeric)
    sms_sent         = Column(Boolean, default=False)
    matched_at       = Column(DateTime, default=func.now())

class MatchRequest(BaseModel):
    job_id: int
    skills: List[str]
    budget: float

class MatchResult(BaseModel):
    freelancer_id: int
    name: str
    score: float
    sms_sent: bool

class MatchResponse(BaseModel):
    job_id: int
    matches: List[MatchResult]