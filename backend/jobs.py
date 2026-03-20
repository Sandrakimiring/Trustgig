from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.services import matcher_client, sms_service

router = APIRouter()


async def _run_matching(job_id: int, job_skills: str, db: Session):
    """
    Background task: call ML matcher → save results → notify freelancers.
    Runs after the job creation response has already been returned to the client.
    """
    matches = await matcher_client.get_matches(job_id, job_skills, db)
    saved = crud.save_matches(db, job_id, matches)

    job = crud.get_job(db, job_id)
    for match in saved:
        freelancer = crud.get_user(db, match.freelancer_id)
        if freelancer:
            msg = sms_service.sms_new_match(
                freelancer_name=freelancer.name,
                job_title=job.title,
                budget=job.budget,
                job_id=job_id,
            )
            sms_service.send_sms(freelancer.phone, msg)
            crud.mark_match_notified(db, match.id)


router = APIRouter()


@router.post("/", response_model=schemas.JobOut, status_code=201)
async def create_job(
    job: schemas.JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    client = crud.get_user(db, job.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client.role != "client":
        raise HTTPException(status_code=400, detail="Only clients can post jobs")

    db_job = crud.create_job(db, job)

    # Fire matching in the background — don't make the client wait
    background_tasks.add_task(
        _run_matching, db_job.id, db_job.skills_required or "", db
    )

    return db_job


@router.get("/", response_model=List[schemas.JobOut])
def list_jobs(status: str = None, db: Session = Depends(get_db)):
    return crud.get_jobs(db, status=status)


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/matches", response_model=List[schemas.MatchWithFreelancer])
def get_job_matches(job_id: int, db: Session = Depends(get_db)):
    """Return ranked match results for a job, enriched with freelancer info."""
    if not crud.get_job(db, job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    matches = crud.get_matches_for_job(db, job_id)
    result = []
    for m in matches:
        freelancer = crud.get_user(db, m.freelancer_id)
        if freelancer:
            result.append(schemas.MatchWithFreelancer(
                freelancer_id=m.freelancer_id,
                score=m.score,
                name=freelancer.name,
                phone=freelancer.phone,
                skills=freelancer.skills,
                location=freelancer.location,
                notified=m.notified,
            ))
    return result