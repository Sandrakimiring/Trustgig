from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.services import sms_service

router = APIRouter()


@router.post("/{job_id}/apply", response_model=schemas.ApplicationOut, status_code=201)
def apply_to_job(
    job_id: int,
    payload: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
):
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail="Job is not open for applications")

    freelancer = crud.get_user(db, payload.freelancer_id)
    if not freelancer:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    if freelancer.role != "freelancer":
        raise HTTPException(status_code=400, detail="Only freelancers can apply")

    if crud.get_application_by_job_and_freelancer(db, job_id, payload.freelancer_id):
        raise HTTPException(status_code=400, detail="Already applied to this job")

    return crud.create_application(db, job_id, payload.freelancer_id)


@router.get("/{job_id}/applications", response_model=List[schemas.ApplicationOut])
def get_applications(job_id: int, db: Session = Depends(get_db)):
    if not crud.get_job(db, job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return crud.get_applications_for_job(db, job_id)


@router.patch("/applications/{application_id}/status")
def update_status(
    application_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    if status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'accepted' or 'rejected'")

    app = crud.update_application_status(db, application_id, status)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Notify freelancer if accepted
    if status == "accepted":
        freelancer = crud.get_user(db, app.freelancer_id)
        job = crud.get_job(db, app.job_id)
        if freelancer and job:
            msg = sms_service.sms_application_accepted(freelancer.name, job.title)
            sms_service.send_sms(freelancer.phone, msg)

    return app