# type: ignore  # pyright: ignore -- runtime deps resolved via sys.path, not IDE-visible
"""
fix_corrupted_skills.py
=======================
One-time script to repair corrupted skills data in the production PostgreSQL DB.

ROOT CAUSE: skills and skills_required were stored as character arrays (e.g.
  ["[", '"', "p", "y", "t", "h", "o", "n", '"', "]"])
instead of proper string arrays (e.g. ["python", "data analysis"]).

This happened because the signup/create_job code did:
  skills = user.skills.split(",")   → correct Python list
But SQLAlchemy's ARRAY(String) column received a stringified list
  str(["python"]) → '["python"]' → iterated char-by-char when stored.

HOW TO RUN:
  Set DATABASE_URL env var to the production PostgreSQL URL, then:
    python fix_corrupted_skills.py
"""

import os
import re
import ast
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://trustgig_db_user:uYRr6hetpwfHfoxsmdFGn7knlS5k5xy6"
    "@dpg-d6qr4a5m5p6s73e8mpg0-a.oregon-postgres.render.com/trustgig_db"
)

engine = create_engine(DATABASE_URL)


def parse_corrupted_skills(char_array: list) -> list[str]:
    """Convert a char-array like ['[','"','p','y','t','h','o','n','"',']'] 
    back into ['python']."""
    if not char_array:
        return []
    
    # If already clean (no structural chars), return as-is
    if not any(c in char_array for c in ['[', ']', '{', '}']):
        return [s for s in char_array if s.strip()]
    
    # Reconstruct the original string and parse it
    joined = "".join(char_array)
    
    # Handle both JSON array format ["a","b"] and set format {"a","b"}
    joined = joined.replace('{', '[').replace('}', ']')
    
    try:
        parsed = ast.literal_eval(joined)
        if isinstance(parsed, (list, tuple)):
            return [s.strip() for s in parsed if s.strip()]
    except Exception:
        pass
    
    # Fallback: naive split on commas, strip quotes/brackets
    cleaned = re.sub(r'[\[\]{}"\']', '', joined)
    return [s.strip() for s in cleaned.split(',') if s.strip()]


def fix_all():
    with engine.connect() as conn:
        # ── Fix user skills ────────────────────────────────────────────────────
        print("\n[1/3] Checking user skills...")
        users = conn.execute(text("SELECT id, name, skills FROM users")).fetchall()
        
        fixed_users: int = 0
        for user in users:
            uid, name, skills = user.id, user.name, user.skills
            if not skills:
                continue
            
            # Detect corruption: skills is a char array (has '[' or '{' or '"' elements)
            is_corrupted = any(
                isinstance(s, str) and s in ('[', ']', '{', '}', '"', "'")
                for s in skills
            )
            
            if is_corrupted:
                fixed = parse_corrupted_skills(skills)
                print(f"  User #{uid} ({name}): {skills[:5]}... -> {fixed}")
                conn.execute(
                    text("UPDATE users SET skills = :skills WHERE id = :uid"),
                    {"skills": fixed, "uid": uid}
                )
                fixed_users += 1  # type: ignore[operator]
            else:
                print(f"  User #{uid} ({name}): OK  {skills}")
        
        print(f"  Fixed {fixed_users} user skill records.\n")
        
        # ── Fix job skills_required ────────────────────────────────────────────
        print("[2/3] Checking job skills_required...")
        jobs = conn.execute(text("SELECT id, title, skills_required FROM jobs")).fetchall()
        
        fixed_jobs: int = 0
        for job in jobs:
            jid, title, skills = job.id, job.title, job.skills_required
            if not skills:
                continue
            
            is_corrupted = any(
                isinstance(s, str) and s in ('[', ']', '{', '}', '"', "'")
                for s in skills
            )
            
            if is_corrupted:
                fixed = parse_corrupted_skills(skills)
                print(f"  Job #{jid} ({title}): {skills[:5]}... -> {fixed}")
                conn.execute(
                    text("UPDATE jobs SET skills_required = :skills WHERE id = :jid"),
                    {"skills": fixed, "jid": jid}
                )
                fixed_jobs += 1  # type: ignore[operator]
            else:
                print(f"  Job #{jid} ({title}): OK  {skills}")
        
        print(f"  Fixed {fixed_jobs} job skills_required records.\n")

        # ── Add missing columns if they don't exist ───────────────────────────
        print("[3/3] Ensuring schema columns exist...")
        
        # Add similarity_score to matches if missing
        try:
            conn.execute(text(
                "ALTER TABLE matches ADD COLUMN IF NOT EXISTS similarity_score FLOAT"
            ))
            print("  matches.similarity_score: ensured")
        except Exception as e:
            print(f"  matches.similarity_score: {e}")

        # Add score to matches if missing
        try:
            conn.execute(text(
                "ALTER TABLE matches ADD COLUMN IF NOT EXISTS score FLOAT DEFAULT 0.0"
            ))
            print("  matches.score: ensured")
        except Exception as e:
            print(f"  matches.score: {e}")
        
        # Backfill score from final_score
        conn.execute(text(
            "UPDATE matches SET score = final_score WHERE score IS NULL OR score = 0"
        ))
        print("  matches.score: backfilled from final_score")
        
        conn.commit()
        print("\n✅ All fixes applied successfully!")


if __name__ == "__main__":
    fix_all()
