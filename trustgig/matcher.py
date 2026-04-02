from sqlalchemy.orm import Session
from trustgig.models import User, Job, Match
from trustgig.embedder import get_top_n_by_vector
from trustgig.scorer import compute_reliability, compute_final_score
from datetime import datetime, timezone


def _compute_budget_match(freelancer_rate: float | None, job_budget: float) -> float:
  
    if freelancer_rate is None or freelancer_rate <= 0:
        return 1.0                                   # no rate info → neutral
    if freelancer_rate <= job_budget:
        return 1.0
    # penalise proportionally — a rate 2× the budget scores 0.5, etc.
    return round(min(1.0, job_budget / freelancer_rate), 4)


def get_top_matches(
    job_id: int,
    job_skills: list,
    job_budget: float,                               
    db: Session,
    top_n: int = 3,
) -> list:
    """
    Find the best freelancers for a job using semantic vector search
    followed by composite scoring (skill fit + reliability + budget).
    """
    print(f"\n[Matcher] Starting match for job_id={job_id}")
    print(f"[Matcher] Required skills : {job_skills}")
    print(f"[Matcher] Budget          : ${job_budget}")

    #  load freelancers 
    freelancers = db.query(User).filter(User.role == "freelancer").all()
    if not freelancers:
        print("[Matcher] No freelancers found in database.")
        return []
    print(f"[Matcher] {len(freelancers)} freelancers in DB.")

    # ─ vector search → top 20 candidates 
    candidates = get_top_n_by_vector(
        job_skills=job_skills,
        freelancers=freelancers,
        top_n=20,
    )
    if not candidates:
        print("[Matcher] Vector search returned no candidates.")
        return []

    print(f"[Matcher] Vector search returned {len(candidates)} candidates.")

    # ── score each candidate 
    results = []
    for candidate in candidates:
        freelancer = candidate["freelancer_obj"]

        vector_similarity = candidate["vector_similarity"]

        reliability = compute_reliability(
            jobs_applied=freelancer.jobs_applied or 0,
            jobs_completed=freelancer.jobs_completed or 0,
            last_completed=freelancer.last_completed,
        )

       
        budget_match = _compute_budget_match(
            freelancer_rate=getattr(freelancer, "hourly_rate", None),
            job_budget=job_budget,
        )

        final_score = compute_final_score(vector_similarity, reliability, budget_match)

        print(
            f"[Matcher] {freelancer.name}: "
            f"vector_similarity={vector_similarity:.4f}, "
            f"reliability={reliability:.4f}, "
            f"budget_match={budget_match:.4f}, "
            f"final_score={final_score:.4f}"
        )

        results.append({
            "freelancer_id":     freelancer.id,
            "name":              freelancer.name,
            "phone":             freelancer.phone,
            "vector_similarity": vector_similarity,   
            "reliability":       reliability,
            "budget_match":      budget_match,
            "final_score":       final_score,
        })

    # sort and return top_n 
    results.sort(key=lambda x: x["final_score"], reverse=True)
    top_matches = results[:top_n]

    print(f"[Matcher] Top {top_n}: {[r['name'] for r in top_matches]}")
    return top_matches



def save_matches_to_db(job_id: int, matches: list, db: Session):
    saved = 0
    for match in matches:
        existing = db.query(Match).filter(
            Match.job_id       == job_id,
            Match.freelancer_id == match["freelancer_id"]
        ).first()

        if existing:
            print(
                f"[Matcher] Skipping duplicate: "
                f"job_id={job_id} freelancer_id={match['freelancer_id']}"
            )
            continue

        db_match = Match(
            job_id            = job_id,
            freelancer_id     = match["freelancer_id"],
            final_score       = match["final_score"],
            vector_similarity = match["vector_similarity"],
            reliability       = match["reliability"],
            sms_sent          = match.get("sms_sent", False),
        )
        db.add(db_match)
        saved += 1

    db.commit()
    print(f"[Matcher] Saved {saved} new matches for job_id={job_id}")