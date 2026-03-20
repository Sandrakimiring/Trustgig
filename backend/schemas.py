'''This file defines your API data schemas using Pydantic.
It controls what data your API accepts (input validation)
It controls what data your API returns (response formatting)

If your models.py file defines the database structure,
this file defines the API contract between the frontend and backend.

It is used by FastAPI + Pydantic.'''
from pydantic import BaseModel, validator, field_validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    phone: str
    role: str
    skills: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v):
        if v not in ("client", "freelancer"):
            raise ValueError("role must be 'client' or 'freelancer'")
        return v


class UserOut(BaseModel):
    id: int
    name: str
    phone: str
    role: str
    skills: Optional[str]
    experience: Optional[str]
    location: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

class JobCreate(BaseModel):
    client_id: int
    title: str
    description: Optional[str] = None
    skills_required: Optional[str] = None
    budget: float


class JobOut(BaseModel):
    id: int
    client_id: int
    title: str
    description: Optional[str]
    skills_required: Optional[str]
    budget: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ApplicationCreate(BaseModel):
    freelancer_id: int          # job_id comes from the URL path


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    freelancer_id: int
    similarity_score: Optional[float]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EscrowFund(BaseModel):
    job_id: int
    amount: float
    phone: Optional[str] = None 


class EscrowRelease(BaseModel):
    job_id: int


class EscrowOut(BaseModel):
    id: int
    job_id: int
    amount: float
    status: str
    funded_at: Optional[datetime]
    released_at: Optional[datetime]

    model_config = {"from_attributes": True}

class MatchResult(BaseModel):
    """Shape Engineer B returns from the ML service."""
    freelancer_id: int
    score: float


class MatchOut(BaseModel):
    id: int
    job_id: int
    freelancer_id: int
    score: float
    notified: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchWithFreelancer(BaseModel):
    """Match result enriched with freelancer details — used in API responses."""
    freelancer_id: int
    score: float
    name: str
    phone: str
    skills: Optional[str]
    location: Optional[str]
    notified: str

    model_config = {"from_attributes": True}

class NotificationOut(BaseModel):
    phone: str
    message: str
    status: str