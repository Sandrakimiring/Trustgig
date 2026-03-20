"""
routes/notifications.py
────────────────────────
Endpoints for manually triggering notifications and
the GET /match/{job_id} endpoint that Engineer B's spec requires.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.services import sms_service

router = APIRouter()


@router.get("/match/{job_id}", response_model=List[schemas.MatchWithFreelancer])
def get_matches(job_id: int, db: Session = Depends(get_db)):
    """
    The canonical endpoint Engineer B's spec defines.
    Returns ranked freelancer matches for a job.
    Identical to GET /jobs/{job_id}/matches — exposed here for Engineer B's convenience.
    """
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


@router.post("/notify/{job_id}")
def notify_matched_freelancers(job_id: int, db: Session = Depends(get_db)):
    """
    Manually re-trigger SMS notifications for all matched freelancers on a job.
    Useful if initial notifications failed or for testing.
    """
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    matches = crud.get_matches_for_job(db, job_id)
    if not matches:
        return {"message": "No matches found for this job", "notified": 0}

    count = 0
    for match in matches:
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
            count += 1

    return {"message": f"Notified {count} freelancers", "job_id": job_id, "notified": count}
    