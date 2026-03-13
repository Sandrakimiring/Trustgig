from datetime import datetime, timezone

def get_recency_weight(last_completed) -> float:
    if last_completed is None:
        return 0.6
 
    now = datetime.now(timezone.utc)

    if last_completed.tzinfo is None:
        last_completed = last_completed.replace(tzinfo=timezone.utc)
 
    days_since = (now - last_completed).days
 
    if days_since <= 30:
        return 1.0
    elif days_since <= 90:
        return 0.8
    else:
        return 0.6
    

def compute_reliability(jobs_applied: int, jobs_completed: int, last_completed) -> float:
    if jobs_applied == 0 or jobs_applied is None:
        return 0.7

    completion_rate = jobs_completed / jobs_applied
    recency = get_recency_weight(last_completed)
    reliability = completion_rate * recency

    return round(min(max(reliability, 0.0), 1.0), 2)

def compute_final_score(similarity: float, reliability: float) -> float:


    final_score = (similarity * 0.6) + (reliability * 0.4)
    return round(final_score, 2)