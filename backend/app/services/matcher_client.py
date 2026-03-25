from sqlalchemy.orm import Session
from models import User, Job, Match
from services.vectorizer import compute_similarity
from services.scorer import compute_reliability, compute_final_score

def parse_skills(skills):
    if not skills:
        return []
    if isinstance(skills, list):
        return skills
    return [s.strip() for s in skills.split(",") if s.strip()]

def get_top_matches(job_id, job_skills, db, top_n=3):
    job_skills_list = parse_skills(job_skills) if isinstance(job_skills, str) else (job_skills or [])
    freelancers = db.query(User).filter(User.role == "freelancer").all()
    if not freelancers:
        return []
    results = []
    for f in freelancers:
        if not f.skills:
            continue
        freelancer_skills = parse_skills(f.skills) if isinstance(f.skills, str) else (f.skills or [])
        similarity = compute_similarity(job_skills_list, freelancer_skills)
        reliability = compute_reliability(
            jobs_applied=f.jobs_applied or 0,
            jobs_completed=f.jobs_completed or 0,
            last_completed=None   # last_completed not tracked in backend User model
        )
        final_score = compute_final_score(similarity, reliability)
        results.append({
            "freelancer_id": f.id,
            "name": f.name,
            "phone": f.phone,
            "similarity": similarity,
            "reliability": reliability,
            "final_score": final_score,
        })
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_n]

def save_matches_to_db(job_id, matches, db):
    for match in matches:
        db_match = Match(
            job_id=job_id,
            freelancer_id=match["freelancer_id"],
            score=match["final_score"],
            similarity_score=match.get("similarity"),
            final_score=match["final_score"],
            sms_sent=match.get("sms_sent", False),
        )
        db.add(db_match)
    db.commit()
