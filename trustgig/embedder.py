import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Global variable to hold the embedding model so it only loads once
_model = None


def _get_model() -> SentenceTransformer:
    global _model
    # If the model hasn't been loaded yet, load it
    if _model is None:
        print("[Embedder] Loading sentence-transformer model…")
        # Load a pretrained sentence embedding model that converts text into vectors
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Embedder] Model loaded.")
    # Return the cached model
    return _model

# Cache for storing FAISS indices so they don't have to be rebuilt every time
_index_cache: dict = {}


def _skills_to_sentence(skills: list[str]) -> str:
    """Convert a skill list into a plain sentence for embedding."""
    # Skills may come as ["python", "machine_learning"]
    # Replace underscores and join into a readable sentence
    return " ".join(s.replace("_", " ") for s in skills if s)


def embed_text(text: str) -> np.ndarray:
    """Return a normalised float32 vector for a single text string."""
    # Convert text into a vector using the embedding model
    vec = _get_model().encode(text, convert_to_numpy=True)

    # Normalize the vector so cosine similarity can be computed using inner product
    vec = vec / (np.linalg.norm(vec) + 1e-10)

    # Convert to float32 because FAISS requires this format
    return vec.astype(np.float32)


def _build_index(valid: list) -> tuple:
    """
    Embed all freelancers and build a FAISS IndexFlatIP.
    Returns (index, freelancer_matrix) so callers can reuse both.
    """

    # Convert each freelancer's skill list into a sentence
    sentences = [_skills_to_sentence(f.skills) for f in valid]

    # Generate embeddings for all freelancer skill sentences
    raw_vecs  = _get_model().encode(sentences, convert_to_numpy=True)

    # Normalize vectors so inner product equals cosine similarity
    norms     = np.linalg.norm(raw_vecs, axis=1, keepdims=True) + 1e-10
    matrix    = (raw_vecs / norms).astype(np.float32)

    # Determine the vector dimension
    dim   = matrix.shape[1]

    # Create a FAISS index using inner product similarity
    index = faiss.IndexFlatIP(dim)

    # Add all freelancer vectors to the FAISS index
    index.add(matrix)

    # Return both the FAISS index and the matrix of embeddings
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
            "vector_similarity": float,
            "freelancer_obj":   User,
        }
    """

    # Filter freelancers to only those who actually have skills listed
    valid = [f for f in freelancers if f.skills]

    # If no freelancers have skills, there is nothing to match against
    if not valid:
        print("[Embedder] No freelancers with skills found.")
        return []

    # Convert job skills into a sentence
    job_sentence = _skills_to_sentence(job_skills)

    # Embed the job sentence into a normalized vector
    job_vec      = embed_text(job_sentence)

    # Print debug information showing what the job embedding represents
    print(f"[Embedder] Job sentence : '{job_sentence}'")
    print(f"[Embedder] Job vec shape: {job_vec.shape}")

    # Create a cache key based on freelancer IDs
    # This allows reusing the FAISS index if the freelancer pool hasn't changed
    cache_key = tuple(sorted(f.id for f in valid))

    # If this freelancer set hasn't been indexed yet, build the FAISS index
    if cache_key not in _index_cache:
        print(f"[Embedder] Building FAISS index for {len(valid)} freelancers…")
        _index_cache.clear()
        _index_cache[cache_key] = (_build_index(valid), valid)
    else:
        print(f"[Embedder] Reusing cached FAISS index ({len(valid)} freelancers).")

    # Retrieve the cached index and freelancer list
    (index, _matrix), cached_valid = _index_cache[cache_key]

    # Determine how many results to return
    k = min(top_n, len(cached_valid))

    # Search the FAISS index using the job vector
    # FAISS returns similarity scores and indices of matching freelancers
    scores, indices = index.search(job_vec.reshape(1, -1), k)

    results = []

    # Loop through each returned match
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):

        # Get the matched freelancer object
        freelancer = cached_valid[idx]

        # Ensure similarity score is non-negative and round it for readability
        vector_similarity = round(float(max(0.0, score)), 4)

        # Print ranking debug information
        print(
            f"[Embedder] #{rank+1:>2} {freelancer.name}: "
            f"vector_similarity={vector_similarity:.4f} | skills={freelancer.skills}"
        )

        # Store the result with relevant freelancer information
        results.append({
            "freelancer_id":     freelancer.id,
            "name":              freelancer.name,
            "phone":             freelancer.phone,
            "vector_similarity": vector_similarity,
            "freelancer_obj":    freelancer,
        })

    # Return the ranked list of freelancers
    return results