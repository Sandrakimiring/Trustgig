"""
TrustGig Engineer B Test Suite
Run from project root: python tests.py

Tests:
  1. Vectorizer - skill normalization and similarity
  2. Scorer - reliability and final score calculation
  3. Notifier - SMS formatting and sending
"""

import sys
sys.path.insert(0, "trustgig")

from datetime import datetime, timezone, timedelta


def test_vectorizer():
    print("\n" + "=" * 50)
    print("=== Testing Vectorizer ===")
    print("=" * 50)

    from vectorizer import normalize_skills, compute_similarity

    # Test normalize_skills
    print("\n[Test] normalize_skills()")

    test_skills = ["Python", "  PANDAS  ", "data-analysis"]
    result = normalize_skills(test_skills)
    print(f"  Input:  {test_skills}")
    print(f"  Output: {result}")
    assert result == ["python", "pandas", "data_analysis"]
    print("  [OK] Basic normalization works")

    # Test deduplication
    dup_skills = ["python", "Python", "PYTHON"]
    result = normalize_skills(dup_skills)
    assert len(result) == 1
    print("  [OK] Deduplication works")

    # Test aliases
    print("\n[Test] Skill aliases")
    alias_tests = [
        (["python3"], ["python"]),
        (["js"], ["javascript"]),
        (["node.js"], ["nodejs"]),
        (["postgres"], ["postgresql"]),
        (["ml"], ["machine_learning"]),
    ]
    for input_skills, expected in alias_tests:
        result = normalize_skills(input_skills)
        assert result == expected
        print(f"  [OK] {input_skills[0]} -> {expected[0]}")

    # Test compute_similarity
    print("\n[Test] compute_similarity()")

    sim = compute_similarity(["python", "pandas"], ["python", "pandas"])
    print(f"  Exact match: {sim}")
    assert sim == 1.0
    print("  [OK] Exact match = 1.0")

    sim = compute_similarity(["python", "pandas"], ["python", "pandas", "excel"])
    print(f"  Partial match: {sim}")
    assert 0.7 < sim < 0.9
    print("  [OK] Partial match works")

    sim = compute_similarity(["python", "pandas"], ["javascript", "react"])
    print(f"  No overlap: {sim}")
    assert sim == 0.0
    print("  [OK] No match = 0.0")

    sim = compute_similarity(["python3"], ["python"])
    print(f"  Alias match: {sim}")
    assert sim == 1.0
    print("  [OK] Aliases work in similarity")

    print("\n[VECTORIZER] All tests passed!")


def test_scorer():
    print("\n" + "=" * 50)
    print("=== Testing Scorer ===")
    print("=" * 50)

    from scorer import get_recency_weight, compute_reliability, compute_final_score

    # Test recency weight
    print("\n[Test] get_recency_weight()")

    recent = datetime.now(timezone.utc) - timedelta(days=5)
    weight = get_recency_weight(recent)
    print(f"  5 days ago: {weight}")
    assert weight == 1.0
    print("  [OK] Recent (<=30 days) = 1.0")

    medium = datetime.now(timezone.utc) - timedelta(days=60)
    weight = get_recency_weight(medium)
    print(f"  60 days ago: {weight}")
    assert weight == 0.8
    print("  [OK] Medium (31-90 days) = 0.8")

    old = datetime.now(timezone.utc) - timedelta(days=120)
    weight = get_recency_weight(old)
    print(f"  120 days ago: {weight}")
    assert weight == 0.6
    print("  [OK] Old (>90 days) = 0.6")

    weight = get_recency_weight(None)
    print(f"  No history: {weight}")
    assert weight == 0.6
    print("  [OK] No history = 0.6")

    # Test reliability
    print("\n[Test] compute_reliability()")

    rel = compute_reliability(10, 8, datetime.now(timezone.utc))
    print(f"  8/10 completed, recent: {rel}")
    assert rel == 0.8
    print("  [OK] High completion rate")

    rel = compute_reliability(10, 2, datetime.now(timezone.utc))
    print(f"  2/10 completed, recent: {rel}")
    assert rel == 0.2
    print("  [OK] Low completion rate")

    rel = compute_reliability(0, 0, None)
    print(f"  New freelancer: {rel}")
    assert rel == 0.7
    print("  [OK] New freelancer gets 0.7 default")

    # Test final score
    print("\n[Test] compute_final_score()")

    score = compute_final_score(1.0, 1.0)
    print(f"  Perfect scores (1.0, 1.0): {score}")
    assert score == 1.0

    score = compute_final_score(0.8, 0.7)
    expected = round(0.8 * 0.6 + 0.7 * 0.4, 2)
    print(f"  Mixed scores (0.8, 0.7): {score}")
    assert score == expected
    print("  [OK] Final score = 0.6*similarity + 0.4*reliability")

    print("\n[SCORER] All tests passed!")


def test_notifier_format():
    print("\n" + "=" * 50)
    print("=== Testing Notifier (Format Only) ===")
    print("=" * 50)

    from notifier import format_sms

    print("\n[Test] format_sms()")

    msg = format_sms("Python Data Cleaning", 40.0, 0.85)
    print(f"\n  Sample SMS message:")
    print("  " + "-" * 30)
    for line in msg.split("\n"):
        print(f"  | {line}")
    print("  " + "-" * 30)

    assert "New Gig Match!" in msg
    assert "Python Data Cleaning" in msg
    assert "$40" in msg
    assert "85%" in msg
    assert "Reply 1 to apply" in msg
    assert "Reply 2 to ignore" in msg
    print("\n  [OK] SMS format contains all required fields")

    print("\n[NOTIFIER FORMAT] Test passed!")


def test_sms_send(phone: str):
    print("\n" + "=" * 50)
    print("=== Testing SMS Send (Live) ===")
    print("=" * 50)

    from notifier import send_match_sms

    print(f"\n  Sending test SMS to: {phone}")
    print("  Check your Africa's Talking simulator!\n")

    result = send_match_sms(
        phone=phone,
        job_title="Python Data Cleaning",
        budget=40.0,
        score=0.85
    )

    if result:
        print("\n  [OK] SMS sent successfully!")
    else:
        print("\n  [FAILED] SMS failed to send")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TrustGig Engineer B Tests")
    parser.add_argument("--sms", type=str, help="Phone number to send test SMS (e.g., +254712345678)")
    args = parser.parse_args()

    # Always run these tests
    test_vectorizer()
    test_scorer()
    test_notifier_format()

    # Only send SMS if phone number provided
    if args.sms:
        test_sms_send(args.sms)
    else:
        print("\n" + "-" * 50)
        print("To test SMS sending, run:")
        print("  python tests.py --sms +254XXXXXXXXX")
        print("-" * 50)

    print("\n" + "=" * 50)
    print("=== ALL TESTS COMPLETED ===")
    print("=" * 50)
