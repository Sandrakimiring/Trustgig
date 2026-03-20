from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.services import sms_service, payments_service

router = APIRouter()


@router.post("/fund", response_model=schemas.EscrowOut, status_code=201)
def fund_escrow(payload: schemas.EscrowFund, db: Session = Depends(get_db)):
    job = crud.get_job(db, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if crud.get_escrow_by_job(db, payload.job_id):
        raise HTTPException(status_code=400, detail="Escrow already exists for this job")

    escrow = crud.create_escrow(db, payload.job_id, payload.amount)
    crud.update_job_status(db, payload.job_id, "in_progress")

    # Optional STK push if client's phone provided
    if payload.phone:
        payments_service.request_stk_push(
            phone=payload.phone,
            amount=payload.amount,
            account_ref=f"JOB-{payload.job_id}",
        )

    # Notify client
    client = crud.get_user(db, job.client_id)
    if client:
        msg = sms_service.sms_escrow_funded(client.name, job.title, payload.amount)
        sms_service.send_sms(client.phone, msg)

    return escrow


@router.post("/release", response_model=schemas.EscrowOut)
def release_payment(payload: schemas.EscrowRelease, db: Session = Depends(get_db)):
    escrow = crud.get_escrow_by_job(db, payload.job_id)
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found for this job")
    if escrow.status != "funded":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot release escrow with status '{escrow.status}'"
        )

    escrow = crud.release_escrow(db, payload.job_id)
    crud.update_job_status(db, payload.job_id, "completed")

    # Find accepted freelancer and pay them
    job = crud.get_job(db, payload.job_id)
    accepted_app = next(
        (a for a in crud.get_applications_for_job(db, payload.job_id) if a.status == "accepted"),
        None,
    )
    if accepted_app:
        freelancer = crud.get_user(db, accepted_app.freelancer_id)
        if freelancer:
            payments_service.disburse_payment(
                phone=freelancer.phone,
                amount=escrow.amount,
                narration=f"Payment for: {job.title}",
            )
            msg = sms_service.sms_payment_released(freelancer.name, escrow.amount, job.title)
            sms_service.send_sms(freelancer.phone, msg)

    return escrow


@router.get("/{job_id}", response_model=schemas.EscrowOut)
def get_escrow(job_id: int, db: Session = Depends(get_db)):
    escrow = crud.get_escrow_by_job(db, job_id)
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found for this job")
    return escrow