"""
ai_routes/ai_features.py
========================
Five AI-powered features for the TrustGig platform.
Now using OpenAI instead of Anthropic Claude.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import openai
from openai import AsyncOpenAI

router = APIRouter()

# ====================== CONFIG ======================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set in environment variables.")

# Recommended models:
# - "gpt-4o-mini"     → Best balance (fast + cheap + smart) ← DEFAULT
# - "gpt-4o"          → Highest quality (more expensive)
# - "gpt-4-turbo"     → Good alternative
MODEL = "gpt-4o-mini"

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def call_openai(prompt: str, max_tokens: int = 1000) -> str:
    """Call OpenAI and return the text response."""
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not configured. Add it to your .env file.",
        )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded. Please try again later.")
    except openai.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {str(e)}"
        )


# ── 1. Job Posting Improvement ────────────────────────────────────────────────

class ImproveJobRequest(BaseModel):
    title: str
    description: str
    skills_required: Optional[str] = ""
    budget: Optional[float] = None
    client_name: Optional[str] = "Client"


@router.post("/improve-job")
async def improve_job_posting(req: ImproveJobRequest):
    """Rewrite and enhance a job posting."""
    prompt = f"""You are an expert job posting consultant for TrustGig, a Kenyan freelance marketplace.

A client named "{req.client_name}" has submitted this job posting:

TITLE: {req.title}
DESCRIPTION: {req.description}
SKILLS REQUIRED: {req.skills_required or "Not specified"}
BUDGET: {"KES " + str(int(req.budget)) if req.budget else "Not specified"}

Rewrite and improve this posting. Return your response in this EXACT structure with these headers:

**Improved Title:**
[A clear, specific title]

**Rewritten Description:**
[2-3 sentences, clear scope, plain English]

**Required Skills:**
[Comma-separated list of 3-6 specific skills]

**Suggested Deliverables:**
[3-4 bullet points of concrete deliverables the freelancer should submit]

**Budget Assessment:**
[One sentence: is the budget realistic for Kenyan market rates? Suggest a range if needed. Use KES.]

**Posting Score:** [X/10 — rate the original posting quality and briefly explain]

Keep the tone professional but friendly. All amounts in KES."""

    result = await call_openai(prompt, max_tokens=800)
    return {"feature": "job_improvement", "result": result}


# ── 2. Profile Coaching ───────────────────────────────────────────────────────

class CoachProfileRequest(BaseModel):
    name: str
    skills: List[str]
    experience: Optional[str] = "intermediate"
    location: Optional[str] = "Kenya"
    jobs_applied: int = 0
    jobs_completed: int = 0
    recent_jobs: Optional[List[str]] = []


@router.post("/coach-profile")
async def coach_profile(req: CoachProfileRequest):
    """Analyse freelancer profile and give actionable coaching."""
    completion_rate = (
        round((req.jobs_completed / req.jobs_applied) * 100)
        if req.jobs_applied > 0 else 0
    )
    recent = ", ".join(req.recent_jobs) if req.recent_jobs else "None listed"

    prompt = f"""You are a career coach for TrustGig, a Kenyan freelance marketplace.

Freelancer profile:
- Name: {req.name}
- Skills: {", ".join(req.skills) if req.skills else "None listed"}
- Experience level: {req.experience}
- Location: {req.location}
- Jobs applied: {req.jobs_applied}
- Jobs completed: {req.jobs_completed}
- Completion rate: {completion_rate}%
- Recent work: {recent}

Provide coaching in this EXACT structure:

**Profile Strength:** [Weak / Moderate / Strong] — one sentence why

**Top 3 Actionable Recommendations:**
1. [Specific action to improve match rate]
2. [Specific action to improve match rate]
3. [Specific action to improve match rate]

**Skills Gap Analysis:**
[Which complementary skills would make this freelancer appear in more searches? Name 2-3 specific skills to add.]

**Completion Rate Insight:**
[Comment on their {completion_rate}% completion rate. What does it signal to clients?]

**Quick Win:**
[One thing they can do TODAY to improve their profile]

Be direct, specific, and encouraging. Use plain English. Keep it under 300 words total."""

    result = await call_openai(prompt, max_tokens=600)
    return {"feature": "profile_coaching", "result": result, "completion_rate": completion_rate}


# ── 3. Match Explanation ──────────────────────────────────────────────────────

class ExplainMatchRequest(BaseModel):
    job_title: str
    job_description: str
    job_skills: List[str]
    job_budget: float
    freelancer_name: str
    freelancer_skills: List[str]
    freelancer_experience: Optional[str] = "intermediate"
    freelancer_completion_rate: Optional[float] = None
    vector_similarity: Optional[float] = None
    final_score: Optional[float] = None


@router.post("/explain-match")
async def explain_match(req: ExplainMatchRequest):
    """Explain why a freelancer matches (or doesn't match) a job."""
    score_hint = ""
    if req.final_score is not None:
        score_hint = f"The system's computed match score is {round(req.final_score * 100)}%."

    prompt = f"""You are an AI matching analyst for TrustGig, a Kenyan freelance platform.

JOB:
- Title: {req.job_title}
- Description: {req.job_description}
- Required skills: {", ".join(req.job_skills)}
- Budget: KES {int(req.job_budget)}

FREELANCER:
- Name: {req.freelancer_name}
- Skills: {", ".join(req.freelancer_skills)}
- Experience: {req.freelancer_experience}
- Completion rate: {f"{round(req.freelancer_completion_rate * 100)}%" if req.freelancer_completion_rate else "Unknown"}

{score_hint}

Provide a match analysis in this EXACT structure:

**Match Score: [X]/100**

**Why This Freelancer Fits:**
[2 sentences explaining skill overlap and strengths]

**Potential Concerns:**
[1 sentence on any skill gaps or risks — or "None identified" if strong match]

**Recommendation:**
[One of: "Strong match — highly recommended" / "Good match — worth considering" / "Partial match — review gaps first" / "Weak match — consider other candidates"]

Be honest and specific. Use the freelancer's actual skills in your analysis."""

    result = await call_openai(prompt, max_tokens=400)
    return {"feature": "match_explanation", "result": result}


# ── 4. TrustScore Explanation ─────────────────────────────────────────────────

class TrustScoreRequest(BaseModel):
    name: str
    jobs_applied: int
    jobs_completed: int
    experience: Optional[str] = "intermediate"
    location: Optional[str] = "Kenya"
    skills: Optional[List[str]] = []
    days_since_last_job: Optional[int] = None
    reviews: Optional[List[str]] = []


@router.post("/trust-score")
async def trust_score_explanation(req: TrustScoreRequest):
    """Generate TrustScore explanation."""
    completion_rate = (
        round((req.jobs_completed / req.jobs_applied) * 100)
        if req.jobs_applied > 0 else 0
    )

    if completion_rate >= 90:
        trust_label = "Highly Trusted"
    elif completion_rate >= 70:
        trust_label = "Trusted"
    elif completion_rate >= 50:
        trust_label = "Use With Caution"
    else:
        trust_label = "Not Recommended"

    recency_info = (
        f"{req.days_since_last_job} days since last completed job"
        if req.days_since_last_job is not None
        else "Recency unknown"
    )
    reviews_text = (
        "\n".join(f"- {r}" for r in req.reviews) if req.reviews else "No reviews available"
    )

    prompt = f"""You are TrustGig's reliability analyst. Write a TrustScore report for a client considering hiring this freelancer.

Freelancer: {req.name}
Location: {req.location}
Experience: {req.experience}
Skills: {", ".join(req.skills) if req.skills else "Not listed"}
Jobs applied: {req.jobs_applied}
Jobs completed: {req.jobs_completed}
Completion rate: {completion_rate}%
Activity: {recency_info}
System trust label: {trust_label}

Client reviews/notes:
{reviews_text}

Write a TrustScore report in this EXACT structure:

**TrustScore: {trust_label}**

**Reliability Summary:**
[2-3 sentences. What does their completion rate and history say? Be honest.]

**Strengths:**
[2 bullet points — specific positives from their data]

**Risk Factors:**
[1-2 bullet points — honest concerns, or "No significant risks identified"]

**Client Recommendation:**
[One sentence advising whether to hire and any precautions to take]

Write in plain, professional English. Under 250 words total."""

    result = await call_openai(prompt, max_tokens=500)
    return {
        "feature": "trust_score",
        "result": result,
        "completion_rate": completion_rate,
        "trust_label": trust_label,
    }


# ── 5. Review / Dispute Analysis ──────────────────────────────────────────────

class ReviewAnalysisRequest(BaseModel):
    freelancer_name: str
    reviews: List[str]
    current_completion_rate: Optional[float] = None
    current_trust_label: Optional[str] = None


@router.post("/analyze-reviews")
async def analyze_reviews(req: ReviewAnalysisRequest):
    """Analyze patterns in reviews and suggest TrustScore adjustments."""
    if not req.reviews:
        raise HTTPException(status_code=400, detail="At least one review is required")

    reviews_formatted = "\n".join(f"{i+1}. \"{r}\"" for i, r in enumerate(req.reviews))
    current_score = (
        f"{round(req.current_completion_rate * 100)}% completion rate, label: {req.current_trust_label}"
        if req.current_completion_rate is not None
        else "Not provided"
    )

    prompt = f"""You are TrustGig's dispute and review analyst. Analyze these client reviews for freelancer "{req.freelancer_name}".

Current TrustScore data: {current_score}

Client Reviews:
{reviews_formatted}

Provide a review analysis in this EXACT structure:

**Pattern Summary:**
[2 sentences identifying the dominant patterns across all reviews]

**Positive Patterns Detected:**
[Bullet list — e.g. fast delivery, good communication, quality work. Write "None detected" if absent]

**Negative Patterns Detected:**
[Bullet list — e.g. late delivery, poor communication, scope creep. Write "None detected" if absent]

**Sentiment Breakdown:**
Positive: [X]% | Neutral: [X]% | Negative: [X]%

**TrustScore Adjustment Recommendation:**
[Should the score go up, down, or stay? By how much (e.g. +5 points, -10 points)? One sentence reason.]

**Action Recommendation:**
[What should TrustGig do? Options: "No action needed" / "Send freelancer a warning" / "Highlight as top performer" / "Flag for review"]

Be objective and specific. Reference actual phrases from the reviews."""

    result = await call_openai(prompt, max_tokens=600)
    return {"feature": "review_analysis", "result": result}