from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILL_ALIASES = {
    "python3": "python",
    "py": "python",
    "js": "javascript",
    "node": "nodejs",
    "node.js": "nodejs",
    "react.js": "react",
    "reactjs": "react",
    "postgres": "postgresql",
    "psql": "postgresql",
    "ml": "machine_learning",
    "data cleaning": "data_analysis",
    "data science": "data_analysis",
    "ms excel": "excel",
}


def normalize_skills(skills: list[str]) -> list[str]:
  
    if not skills:
        return []

    result = []
    seen = set()

    for skill in skills:
        clean = skill.lower().strip()
        clean = " ".join(clean.split())   # remove repeated spaces
        clean = clean.replace("-", " ")
        clean = SKILL_ALIASES.get(clean, clean)
        clean = clean.replace(" ", "_")

        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result


def compute_similarity(job_skills: list[str], freelancer_skills: list[str]) -> float:
    job_clean = normalize_skills(job_skills)
    freelancer_clean = normalize_skills(freelancer_skills)

    if not job_clean or not freelancer_clean:
        return 0.0

    job_string = " ".join(job_clean)
    freelancer_string = " ".join(freelancer_clean)

    vectorizer = CountVectorizer(binary=True)
    vectors = vectorizer.fit_transform([job_string, freelancer_string])

    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    return round(float(similarity), 2)