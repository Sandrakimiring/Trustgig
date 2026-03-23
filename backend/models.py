'''This file defines your API data schemas using Pydantic.

In simple terms:
It controls what data your API accepts (input validation)
It controls what data your API returns (response formatting)

If your models.py file defines the database structure,
this file defines the API contract between the frontend and backend.

It is used by FastAPI + Pydantic.'''

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


git class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    role = Column(String(20), nullable=False)           # "client" or "freelancer"
    skills = Column(String(500), nullable=True)         # comma-separated
    experience = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs_posted = relationship("Job", back_populates="client")
    applications = relationship("Application", back_populates="freelancer")
    matches = relationship("Match", back_populates="freelancer")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    skills_required = Column(String(500), nullable=True)
    budget = Column(Float, nullable=False)
    status = Column(String(20), default="open")         # open | in_progress | completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("User", back_populates="jobs_posted")
    applications = relationship("Application", back_populates="job")
    escrow = relationship("Escrow", back_populates="job", uselist=False)
    matches = relationship("Match", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    similarity_score = Column(Float, nullable=True)
    status = Column(String(20), default="pending")      # pending | accepted | rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("job_id", "freelancer_id", name="uq_application_job_freelancer"),
    )

    job = relationship("Job", back_populates="applications")
    freelancer = relationship("User", back_populates="applications")


class Escrow(Base):
    __tablename__ = "escrow"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")      # pending | funded | released
    funded_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("Job", back_populates="escrow")


class Match(Base):
    """
    Populated by Engineer B's ML matching engine.
    Each row = one freelancer candidate for a job, with a similarity score.
    """
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=False)               # 0.0 – 1.0
    notified = Column(String(5), default="no")          # "yes" | "no"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("job_id", "freelancer_id", name="uq_match_job_freelancer"),
    )

    job = relationship("Job", back_populates="matches")
    freelancer = relationship("User", back_populates="matches")

    class Delivery(Base):
    __tablename__ = "deliveries"
    id            = Column(Integer, primary_key=True)
    job_id        = Column(Integer)
    freelancer_id = Column(Integer)
    delivery_link = Column(String)
    message       = Column(String)
    status        = Column(String, default="pending")  # pending | approved | rejected
    delivered_at  = Column(DateTime, default=func.now())