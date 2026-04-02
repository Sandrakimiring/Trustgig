import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


def _skills_to_sentence(skills: list[str]) -> str:
    """
    Convert a skill list into a plain sentence for embedding.
    """
    return " ".join(s.replace("_", " ") for s in skills if s)


def embed_text(text: str) -> np.ndarray:
    """Return a normalised float32 vector for a single text string."""
    vec = _model.encode(text, convert_to_numpy=True)
    # L2-normalise so cosine similarity (required by FAISS IndexFlatIP)
    vec = vec / (np.linalg.norm(vec) + 1e-10)
    return vec.astype(np.float32)


def get_top_n_by_vector(
    job_skills: list[str],
    freelancers: list,          
    top_n: int = 20,
) -> list[dict]:
    """
    Embed the job's required skills and every freelancer's skills,
    run a FAISS inner-product search (= cosine sim on normalised vecs),
    and return the top_n freelancers with their vector similarity score.

    Returns a list of dicts — same shape as matcher.py expects:
        {
            "freelancer_id": int,
            "name": str,
            "phone": str,
            "vector_similarity": float,   # NEW field, 0.0–1.0
            "freelancer_obj": User,        # passed through for scorer
        }
    """
    # filter out freelancers with no skills 
    valid = [f for f in freelancers if f.skills]
    if not valid:
        print("[Embedder] No freelancers with skills found.")
        return []

    #  embed the job
    job_sentence = _skills_to_sentence(job_skills)
    job_vec = embed_text(job_sentence)          # shape: (dim,)
    print(f"[Embedder] Job vector shape: {job_vec.shape}")
    print(f"[Embedder] Job sentence: '{job_sentence}'")

    #  embed every freelancer 
    freelancer_sentences = [
        _skills_to_sentence(f.skills) for f in valid
    ]
    # encode all at once 
    raw_vecs = _model.encode(freelancer_sentences, convert_to_numpy=True)

    # normalise each row
    norms = np.linalg.norm(raw_vecs, axis=1, keepdims=True) + 1e-10
    freelancer_matrix = (raw_vecs / norms).astype(np.float32)  # shape: (N, dim)

    print(f"[Embedder] Embedded {len(valid)} freelancers.")

    # build FAISS index 
    dim = job_vec.shape[0]
    index = faiss.IndexFlatIP(dim)          
    index.add(freelancer_matrix)           

    # search: find top_n closest to job vector 
    k = min(top_n, len(valid))              # can't ask for more than we have
    scores, indices = index.search(
        job_vec.reshape(1, -1), k           # query must be 2D: (1, dim)
    )

    results = []
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
        freelancer = valid[idx]
        sim = float(score)                  
        sim = round(max(0.0, sim), 4)       

        print(
            f"[Embedder] #{rank+1} {freelancer.name}: "
            f"vector_sim={sim:.4f} | skills={freelancer.skills}"
        )

        results.append({
            "freelancer_id":    freelancer.id,
            "name":             freelancer.name,
            "phone":            freelancer.phone,
            "vector_similarity": sim,
            "freelancer_obj":   freelancer,     
        })

    return results