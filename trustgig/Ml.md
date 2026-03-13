# TrustGig Matching Engine (Engineer B)

This module handles AI-based freelancer-job matching and SMS notifications.

## Files

| File | Purpose |
|------|---------|
| `vectorizer.py` | Skill normalization and cosine similarity |
| `scorer.py` | Reliability scoring based on job history |
| `matcher.py` | Main matching algorithm - ranks freelancers |
| `notifier.py` | SMS notifications via Africa's Talking |
| `models.py` | Database models (User, Job, Match) |
| `database.py` | PostgreSQL connection |
| `main.py` | FastAPI endpoints |

## How Matching Works

```
Job Skills: ["python", "pandas"]
                ↓
         Vectorizer
    (normalize + aliases)
                ↓
    Cosine Similarity → 0.85
                ↓
         Scorer
    (reliability score) → 0.80
                ↓
    Final Score = (0.6 × 0.85) + (0.4 × 0.80) = 0.83
                ↓
    Top 3 freelancers get SMS
```

## Key Functions

### vectorizer.py
```python
normalize_skills(["Python3", "JS"]) → ["python", "javascript"]
compute_similarity(job_skills, freelancer_skills) → 0.0 to 1.0
```

### scorer.py
```python
compute_reliability(jobs_applied, jobs_completed, last_completed) → 0.0 to 1.0
compute_final_score(similarity, reliability) → weighted average
```

### matcher.py
```python
get_top_matches(job_id, job_skills, db, top_n=3) → list of top freelancers
save_matches_to_db(job_id, matches, db) → saves to matches table
```

### notifier.py
```python
format_sms(job_title, budget, score) → SMS message string
send_match_sms(phone, job_title, budget, score) → True/False
```

## Scoring Formula

```
final_score = (0.6 × skill_similarity) + (0.4 × reliability)
```

- **Skill similarity (60%)**: How well freelancer skills match job requirements
- **Reliability (40%)**: Job completion rate × recency weight

## Skill Aliases

The system recognizes common variations:

| Input | Normalized |
|-------|------------|
| python3, py | python |
| js | javascript |
| node, node.js | nodejs |
| postgres, psql | postgresql |
| ml | machine_learning |

## SMS Format

```
New Gig Match!
Python Data Cleaning
Budget: $40
Match: 85%

Reply 1 to apply
Reply 2 to ignore
```

## Testing

From project root:
```bash
python tests.py                    # Test matching logic
python tests.py --sms +254XXXXXX   # Test with live SMS
```

## API Endpoints (main.py)

- `POST /match` — Run matching + send SMS + save results
- `GET /match/{job_id}` — Get saved matches for a job
- `GET /health` — Health check

## Environment Variables Needed

```
DATABASE_URL=postgresql://...
AT_USERNAME=sandbox
AT_API_KEY=your_key
```
