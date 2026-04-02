from sqlalchemy.orm import Session
from trustgig.models import User, Job, Match
from trustgig.embedder import get_top_n_by_vector          # NEW
from trustgig.scorer import compute_reliability, compute_final_score
from datetime import datetime, timezone


def get_top_matches(
    job_id: int,
    job_skills: list,
    db: Session,
    top_n: int = 3,
) -> list:
    """
    Find the best freelancers for a job using semantic vector search.
    """
    print(f"\n[Matcher] Starting match for job_id={job_id}")
    print(f"[Matcher] Job requires skills: {job_skills}")

    # load freelancers 
    freelancers = db.query(User).filter(User.role == "freelancer").all()
    if not freelancers:
        print("[Matcher] No freelancers found in database.")
        return []
    print(f"[Matcher] Found {len(freelancers)} total freelancers.")

    # vector search → top 20 candidates 
    candidates = get_top_n_by_vector(
        job_skills=job_skills,
        freelancers=freelancers,
        top_n=20,                           
    )

    if not candidates:
        print("[Matcher] Vector search returned no candidates.")
        return []

    print(f"[Matcher] Vector search returned {len(candidates)} candidates.")

    # score each candidate with scorer.py 
    results = []
    for candidate in candidates:
        freelancer = candidate["freelancer_obj"]

        reliability = compute_reliability(
            jobs_applied=freelancer.jobs_applied or 0,
            jobs_completed=freelancer.jobs_completed or 0,
            last_completed=freelancer.last_completed,
        )

        # final score using vector_similarity 
        vector_sim = candidate["vector_similarity"]
        final_score = compute_final_score(vector_sim, reliability)

        print(
            f"[Matcher] {freelancer.name}: "
            f"vector_sim={vector_sim}, reliability={reliability}, final={final_score}"
        )

        results.append({
            "freelancer_id": freelancer.id,
            "name":          freelancer.name,
            "phone":         freelancer.phone,
            "similarity":    vector_sim,        # keeps same key name for DB save
            "reliability":   reliability,
            "final_score":   final_score,
        })

    # sort and return top_n 
    results.sort(key=lambda x: x["final_score"], reverse=True)
    top_matches = results[:top_n]

    print(f"[Matcher] Top {top_n} matches: {[r['name'] for r in top_matches]}")
    return top_matches


# save_matches_to_db 

def save_matches_to_db(job_id: int, matches: list, db: Session):
    saved = 0
    for match in matches:
        existing = db.query(Match).filter(
            Match.job_id == job_id,
            Match.freelancer_id == match["freelancer_id"]
        ).first()
        if existing:
            print(f"[Matcher] Skipping duplicate: job_id={job_id} freelancer_id={match['freelancer_id']}")
            continue

        db_match = Match(
            job_id=job_id,
            freelancer_id=match["freelancer_id"],
            score=match["final_score"],
            final_score=match["final_score"],
            sms_sent=match.get("sms_sent", False),
        )
        db.add(db_match)
        saved += 1

    db.commit()
    print(f"[Matcher] Saved {saved} new matches to DB for job_id={job_id}")