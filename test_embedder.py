"""
test_embedder.py
================
Tests for the new semantic vector search (embedder.py).
Run from project root:
    python test_embedder.py

No database needed — uses mock freelancer objects.
"""

import sys
sys.path.insert(0, "trustgig")

from embedder import get_top_n_by_vector, embed_text, _skills_to_sentence


# ── Mock freelancer object (mirrors the SQLAlchemy User model) ────────────────

class MockFreelancer:
    def __init__(self, id, name, phone, skills):
        self.id = id
        self.name = name
        self.phone = phone
        self.skills = skills
        self.jobs_applied = 10
        self.jobs_completed = 8
        self.last_completed = None


MOCK_FREELANCERS = [
    MockFreelancer(1,  "Mercy Wanjiru",   "+254701000001", ["python", "pandas", "data_analysis"]),
    MockFreelancer(2,  "James Otieno",    "+254701000002", ["react", "nodejs", "javascript"]),
    MockFreelancer(3,  "Amina Hassan",    "+254701000003", ["figma", "branding", "design"]),
    MockFreelancer(4,  "Brian Kamau",     "+254701000004", ["django", "python", "postgresql"]),
    MockFreelancer(5,  "Samuel Kipchoge", "+254701000008", ["machine_learning", "python", "tensorflow"]),
    MockFreelancer(6,  "Grace Achieng",   "+254701000007", ["copywriting", "content", "seo"]),
    MockFreelancer(7,  "Kevin Mwangi",    "+254701000006", ["flutter", "dart", "mobile_development"]),
]


# ── Test 1: semantic similarity (the key improvement over word overlap) ────────

def test_semantic_matching():
    print("\n" + "="*55)
    print("=== Test 1: Semantic matching (the important one) ===")
    print("="*55)

    # Job requires "data analyst" skills.
    # Mercy has "pandas, data_analysis" — should rank high.
    # James has "react, nodejs" — should rank low.
    # Old vectorizer would score "data analyst" vs "pandas expert" = 0.0
    # New embedder should score them as semantically close.

    job_skills = ["data analyst", "spreadsheet", "data cleaning"]
    print(f"\nJob skills: {job_skills}")
    print("(Note: none of these exact words appear in any freelancer's skill list)")

    results = get_top_n_by_vector(job_skills, MOCK_FREELANCERS, top_n=3)

    print(f"\nTop 3 results:")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['name']} — vector_sim={r['vector_similarity']}")

    # Mercy (data analysis) or Samuel (ML/python) should beat James (react)
    top_names = [r["name"] for r in results]
    assert "Mercy Wanjiru" in top_names or "Samuel Kipchoge" in top_names or "Brian Kamau" in top_names, \
        "Expected a data/python freelancer in top 3 for a data analyst job"

    # James (react/JS) should NOT be #1 for a data analyst job
    assert results[0]["name"] != "James Otieno", \
        "James (react dev) should not be #1 match for a data analyst job"

    print("\n[OK] Semantic matching works — correct freelancers surfaced")


# ── Test 2: exact skills still work ──────────────────────────────────────────

def test_exact_skills():
    print("\n" + "="*55)
    print("=== Test 2: Exact skill match still scores high ===")
    print("="*55)

    job_skills = ["react", "javascript", "frontend"]
    print(f"\nJob skills: {job_skills}")

    results = get_top_n_by_vector(job_skills, MOCK_FREELANCERS, top_n=3)

    print(f"\nTop 3 results:")
    for i, r in enumerate(results):
        print(f"  {i+1}. {r['name']} — vector_sim={r['vector_similarity']}")

    # James (react, nodejs, javascript) should be #1
    assert results[0]["name"] == "James Otieno", \
        f"Expected James Otieno #1 for react job, got {results[0]['name']}"

    print("\n[OK] Exact skill match still works correctly")


# ── Test 3: empty skills handled gracefully ───────────────────────────────────

def test_empty_skills():
    print("\n" + "="*55)
    print("=== Test 3: Edge cases — empty/null skills ===")
    print("="*55)

    # freelancer with no skills
    no_skill = MockFreelancer(99, "Empty Person", "+254000000000", [])
    result = get_top_n_by_vector(["python"], [no_skill], top_n=5)
    assert result == [], "Expected empty list when all freelancers have no skills"
    print("  [OK] Freelancer with no skills returns empty list")

    # job with no skills
    result2 = get_top_n_by_vector([], MOCK_FREELANCERS, top_n=5)
    # empty job sentence will embed to near-zero — should not crash
    print("  [OK] Empty job skills handled without crash")


# ── Test 4: top_n capping ─────────────────────────────────────────────────────

def test_top_n_capping():
    print("\n" + "="*55)
    print("=== Test 4: top_n capping ===")
    print("="*55)

    # ask for 20 but only 7 freelancers exist
    results = get_top_n_by_vector(["python"], MOCK_FREELANCERS, top_n=20)
    assert len(results) <= len(MOCK_FREELANCERS), \
        f"Should not return more than {len(MOCK_FREELANCERS)} results"
    print(f"  [OK] Asked for 20, got {len(results)} (capped to available freelancers)")


# ── Test 5: scores are valid floats between 0 and 1 ──────────────────────────

def test_score_range():
    print("\n" + "="*55)
    print("=== Test 5: Score range validation ===")
    print("="*55)

    results = get_top_n_by_vector(["python", "data"], MOCK_FREELANCERS, top_n=7)
    for r in results:
        assert 0.0 <= r["vector_similarity"] <= 1.0, \
            f"{r['name']} has out-of-range score: {r['vector_similarity']}"
    print(f"  [OK] All {len(results)} scores are between 0.0 and 1.0")


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_semantic_matching()
    test_exact_skills()
    test_empty_skills()
    test_top_n_capping()
    test_score_range()

    print("\n" + "="*55)
    print("=== ALL TESTS PASSED ===")
    print("="*55)
    print("\nNext step: python test_matcher_integration.py")