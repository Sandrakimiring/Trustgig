# matching engine 
from sqlalchemy.orm import Session
from models import User, Job, Match
from vectorizer import compute_similarity
from scorer import compute_reliability, compute_final_score
from datetime import datetime, timezone

def get_top_matches (job_id: int, job_skills: list, db: Session, top_n: int = 3) -> list:
    print(f"\n[Matcher] Starting match for job_id={job_id}")
    print(f"[Matcher] Job requires skills: {job_skills}")

    freelancers = db.query(User).filter(User.role == "freelancer").all()
    if not freelancers:
        print("[Matcher] No freelancers found in database.")
        return []
    print(f"[Matcher] Found {len(freelancers)} freelancers to evaluate.")

    results= []
    for freelancer in freelancers:
        if not freelancer.skills:
            print(f"[Matcher] Skipping {freelancer.name} — no skills listed")
            continue
 
       
        similarity = compute_similarity(job_skills, freelancer.skills)
 
        # Compute how reliable they are based on their history
        reliability = compute_reliability(
            jobs_applied=freelancer.jobs_applied or 0,
            jobs_completed=freelancer.jobs_completed or 0,
            last_completed=freelancer.last_completed
        )
 
        # Combine into final ranking score
        final_score = compute_final_score(similarity, reliability)
 
        print(
            f"[Matcher] {freelancer.name}: "
            f"similarity={similarity}, reliability={reliability}, final={final_score}"
        )
 
        results.append({
            "freelancer_id": freelancer.id,
            "name":          freelancer.name,
            "phone":         freelancer.phone,
            "similarity":    similarity,
            "reliability":   reliability,
            "final_score":   final_score,
        })
 
    # Sort by final_score, highest first ─────────────────────
    results.sort(key=lambda x: x["final_score"], reverse=True)
 
   
    top_matches = results[:top_n]
 
    print(f"[Matcher] Top {top_n} matches: {[r['name'] for r in top_matches]}")
 
    return top_matches
 
 
def save_matches_to_db(job_id: int, matches: list, db: Session):
    
    for match in matches:
        db_match = Match(
            job_id=job_id,
            freelancer_id=match["freelancer_id"],
            similarity_score=match["similarity"],
            final_score=match["final_score"],
            sms_sent=match.get("sms_sent", False),
        )
        db.add(db_match)
 
    db.commit()
    print(f"[Matcher] Saved {len(matches)} matches to DB for job_id={job_id}")
