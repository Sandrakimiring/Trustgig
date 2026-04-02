import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from trustgig.database import get_db, engine, Base
from trustgig.models import User, Job, Match, MatchRequest, MatchResult
from trustgig.matcher import get_top_matches, save_matches_to_db
from trustgig import models 
Base.metadata.create_all(bind=engine)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# app setup
app = FastAPI(
    title="TrustGig Freelance Matching Service",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "TrustGig ML Matching Service",
        "port": 8001
    }

# call when job is posted - match → SMS → save → return results
@app.post("/match", response_model=List[MatchResult])
def match_job(request: MatchRequest, db: Session = Depends(get_db)):

    print(f"\n{'='*50}")
    print(f"[API] POST /match received")
    print(f"[API] job_id={request.job_id}, skills={request.skills}, budget=${request.budget}")

    # get job title for the SMS message
    try:
        job = db.query(Job).filter(Job.id == request.job_id).first()
        job_title = job.title if job else "New gig opportunity"
        print(f"[API] Job title: '{job_title}'")
    except Exception as e:
        print(f"[API] Warning — could not fetch job title: {e}")
        job_title = "New gig opportunity"

    # run matching engine
    try:
        top_matches = get_top_matches(
            job_id=request.job_id,
            job_skills=request.skills,
            db=db
        )
    except Exception as e:
        print(f"[API] Matching engine error: {e}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

    # return if no matches found
    if not top_matches:
        print("[API] No matches found — returning empty list")
        return []

    # SMS is now handled by the Main Web Service to avoid duplicates
    for match in top_matches:
        match["sms_sent"] = False
    # save to DB
    try:
        save_matches_to_db(request.job_id, top_matches, db)
    except Exception as e:
        print(f"[API] Warning — could not save matches to DB: {e}")

    # build and return response
    response = [
        MatchResult(
            freelancer_id=m["freelancer_id"],
            name=m["name"],
            score=m["final_score"],
            sms_sent=m.get("sms_sent", False)
        )
        for m in top_matches
    ]

    print(f"[API] Returning {len(response)} matches to Engineer A")
    print(f"{'='*50}\n")
    return response


# GET /match/{job_id} ──
@app.get("/match/{job_id}")
def get_matches(job_id: int, db: Session = Depends(get_db)):

    print(f"[API] GET /match/{job_id}")

    matches = db.query(Match).filter(Match.job_id == job_id).all()

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No matches found for job_id={job_id}. "
                   f"Call POST /match first for this job."
        )

    result = []
    for m in matches:
        freelancer = db.query(User).filter(User.id == m.freelancer_id).first()
        result.append({
            "freelancer_id": m.freelancer_id,
            "name":          freelancer.name if freelancer else "Unknown",
            "score":         float(m.final_score),
            "sms_sent":      m.sms_sent,
            "matched_at":    m.matched_at.isoformat() if m.matched_at else None
        })

    print(f"[API] Found {len(result)} matches for job_id={job_id}")
    return {"job_id": job_id, "matches": result}
