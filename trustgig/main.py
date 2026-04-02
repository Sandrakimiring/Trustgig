import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from trustgig.database import get_db, engine, Base
from trustgig.models import User, Job, Match, MatchRequest, MatchResult, MatchResponse
from trustgig.matcher import get_top_matches, save_matches_to_db
from trustgig import models

Base.metadata.create_all(bind=engine)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List



app = FastAPI(
    title="TrustGig Freelance Matching Service",
    version="2.0",
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
        "status":  "ok",
        "service": "TrustGig ML Matching Service",
        "port":    8001,
    }

#  POST /match 

@app.post("/match", response_model=List[MatchResult])
def match_job(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Main matching endpoint.
    Triggered when a job is posted by the Main Web Service.
    Runs vector search + composite scoring, persists results, returns top matches.
    """
    print(f"\n{'='*55}")
    print(f"[API] POST /match")
    print(f"[API] job_id={request.job_id} | skills={request.skills} | budget=${request.budget}")

    # run matching engine 
    try:
        top_matches = get_top_matches(
            job_id     = request.job_id,
            job_skills = request.skills,
            job_budget = request.budget,     # FIX: budget is now forwarded and used
            db         = db,
        )
    except Exception as e:
        print(f"[API] Matching engine error: {e}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

    if not top_matches:
        print("[API] No matches found — returning empty list.")
        return []

    # SMS is handled by the Main Web Service to avoid duplicates
    for match in top_matches:
        match["sms_sent"] = False

    try:
        save_matches_to_db(request.job_id, top_matches, db)
    except Exception as e:
        print(f"[API] Warning — could not save matches to DB: {e}")

    response = [
        MatchResult(
            freelancer_id = m["freelancer_id"],
            name          = m["name"],
            score         = m["final_score"],
            sms_sent      = m.get("sms_sent", False),
        )
        for m in top_matches
    ]

    print(f"[API] Returning {len(response)} matches.")
    print(f"{'='*55}\n")
    return response


#  GET /match/{job_id}

@app.get("/match/{job_id}", response_model=MatchResponse)   
def get_matches(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieve previously computed matches for a job.
    Call POST /match first if no matches exist yet.
    """
    print(f"[API] GET /match/{job_id}")

    matches = db.query(Match).filter(Match.job_id == job_id).all()
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No matches found for job_id={job_id}. "
                f"Call POST /match first."
            ),
        )

    result = []
    for m in matches:
        freelancer = db.query(User).filter(User.id == m.freelancer_id).first()
        result.append(
            MatchResult(
                freelancer_id = m.freelancer_id,
                name          = freelancer.name if freelancer else "Unknown",
                score         = float(m.final_score),
                sms_sent      = m.sms_sent,
            )
        )

    print(f"[API] Returning {len(result)} matches for job_id={job_id}")
    return MatchResponse(job_id=job_id, matches=result)