from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from trustgig.database import Base



class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String)
    phone          = Column(String)
    role           = Column(String)           
    skills         = Column(JSON)            
    experience     = Column(String)          
    location       = Column(String)
    hourly_rate    = Column(Float, nullable=True)   
    jobs_completed = Column(Integer, default=0)
    jobs_applied   = Column(Integer, default=0)
    last_completed = Column(DateTime, nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id              = Column(Integer, primary_key=True)
    client_id       = Column(Integer)
    title           = Column(String)
    description     = Column(String)
    skills_required = Column(JSON)            # e.g. ["python", "pandas"]
    budget          = Column(Numeric)
    status          = Column(String, default="open")


class Match(Base):
    __tablename__ = "matches"

    id              = Column(Integer, primary_key=True)
    job_id          = Column(Integer)
    freelancer_id   = Column(Integer)
   
    final_score     = Column(Numeric)
    vector_similarity = Column(Float)         
    reliability     = Column(Float)         
    sms_sent        = Column(Boolean, default=False)
    matched_at      = Column(DateTime, default=func.now())




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
    """Used as the response model for GET /match/{job_id}."""
    job_id: int
    matches: List[MatchResult]