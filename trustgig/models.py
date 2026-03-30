from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from trustgig.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String) 
    role = Column(String)  # 'client' or 'freelancer'
    skills = Column(JSON) 
    experience = Column(String)  # 'beginner', 'intermediate', 'expert'
    location = Column(String)
    jobs_completed = Column(Integer, default=0)
    jobs_applied = Column(Integer, default=0)
    last_completed = Column(DateTime, nullable=True)

class Job(Base):
    # job table fetch skills required for a job 
   
    __tablename__ = "jobs"
 
    id              = Column(Integer, primary_key=True)
    client_id       = Column(Integer)
    title           = Column(String)
    description     = Column(String)
    skills_required = Column(JSON)    # e.g. ["python", "pandas"]
    budget          = Column(Numeric)
    status          = Column(String, default="open")
 
 
class Match(Base):
 
    __tablename__ = "matches"
 
    id               = Column(Integer, primary_key=True)
    job_id           = Column(Integer)
    freelancer_id    = Column(Integer)
    score            = Column(Numeric, default=0.0)   # alias of final_score for backend compat
    similarity_score = Column(Numeric)
    final_score      = Column(Numeric)
    sms_sent         = Column(Boolean, default=False)
    matched_at       = Column(DateTime, default=func.now())

    # how data looks when coming in and going out 


class MatchRequest(BaseModel):
    # the request body for POST /match
    job_id: int
    skills: List[str]         
    budget: float
 
 
class MatchResult(BaseModel):
    # the individual match result returned in GET /match/{job_id}
    freelancer_id: int
    name: str
    score: float               
    sms_sent: bool
 
 
class MatchResponse(BaseModel):
# the response body for GET /match/{job_id}
    job_id: int
    matches: List[MatchResult]
 
