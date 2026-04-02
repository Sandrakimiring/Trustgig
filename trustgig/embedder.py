import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


_model = SentenceTransformer("all-MiniLM-L6-v2")

_index_cache: dict = {}


def _skills_to_sentence(skills: list[str]) -> str:
    """Convert a skill list into a plain sentence for embedding."""
    return " ".join(s.replace("_", " ") for s in skills if s)


def embed_text(text: str) -> np.ndarray:
    """Return a normalised float32 vector for a single text string."""
    vec = _model.encode(text, convert_to_numpy=True)
    vec = vec / (np.linalg.norm(vec) + 1e-10)
    return vec.astype(np.float32)


def _build_index(valid: list) -> tuple:
    """
    Embed all freelancers and build a FAISS IndexFlatIP.
    Returns (index, freelancer_matrix) so callers can reuse both.
    """
    sentences = [_skills_to_sentence(f.skills) for f in valid]
    raw_vecs  = _model.encode(sentences, convert_to_numpy=True)
    norms     = np.linalg.norm(raw_vecs, axis=1, keepdims=True) + 1e-10
    matrix    = (raw_vecs / norms).astype(np.float32)

    dim   = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)
    return index, matrix


def get_top_n_by_vector(
    job_skills: list[str],
    freelancers: list,
    top_n: int = 20,
) -> list[dict]:
    """
    Embed the job's required skills and every freelancer's skills,
    run a FAISS inner-product search (= cosine sim on normalised vecs),
    and return the top_n freelancers with their vector_similarity score.

    Returns a list of dicts:
        {
            "freelancer_id":    int,
            "name":             str,
            "phone":            str,
            "vector_similarity": float,   # 0.0–1.0, consistent name throughout
            "freelancer_obj":   User,
        }
    """
    # FIX: filter out freelancers with no skills
    valid = [f for f in freelancers if f.skills]
    if not valid:
        print("[Embedder] No freelancers with skills found.")
        return []

    # embed the job query 
    job_sentence = _skills_to_sentence(job_skills)
    job_vec      = embed_text(job_sentence)          # shape: (dim,)
    print(f"[Embedder] Job sentence : '{job_sentence}'")
    print(f"[Embedder] Job vec shape: {job_vec.shape}")


    cache_key = tuple(sorted(f.id for f in valid))
    if cache_key not in _index_cache:
        print(f"[Embedder] Building FAISS index for {len(valid)} freelancers…")
        _index_cache.clear()                        # keep memory bounded
        _index_cache[cache_key] = (_build_index(valid), valid)
    else:
        print(f"[Embedder] Reusing cached FAISS index ({len(valid)} freelancers).")

    (index, _matrix), cached_valid = _index_cache[cache_key]


    k = min(top_n, len(cached_valid))
    scores, indices = index.search(job_vec.reshape(1, -1), k)

    results = []
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
        freelancer      = cached_valid[idx]
        vector_similarity = round(float(max(0.0, score)), 4)

        print(
            f"[Embedder] #{rank+1:>2} {freelancer.name}: "
            f"vector_similarity={vector_similarity:.4f} | skills={freelancer.skills}"
        )

        results.append({
            "freelancer_id":     freelancer.id,
            "name":              freelancer.name,
            "phone":             freelancer.phone,
            "vector_similarity": vector_similarity,   
            "freelancer_obj":    freelancer,
        })

    return results