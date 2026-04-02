"""
TrustGig DB Migration Script
Run this ONCE against your Render PostgreSQL to apply all schema fixes.

Usage:
    DATABASE_URL=<your_render_db_url> python migrate.py
"""

import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Set DATABASE_URL environment variable before running this script")

# Render uses postgres:// but psycopg2 needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

migrations = [
    # jobs table
    (
        "Add assigned_freelancer_id to jobs",
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS assigned_freelancer_id INTEGER
        REFERENCES users(id) ON DELETE SET NULL;
        """
    ),
    (
        "Add created_at to jobs",
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
        """
    ),

    # users table
    (
        "Add hourly_rate to users",
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS hourly_rate FLOAT;
        """
    ),

    # matches table — v2 embedder columns
    (
        "Add final_score to matches",
        """
        ALTER TABLE matches
        ADD COLUMN IF NOT EXISTS final_score NUMERIC;
        """
    ),
    (
        "Add vector_similarity to matches",
        """
        ALTER TABLE matches
        ADD COLUMN IF NOT EXISTS vector_similarity FLOAT;
        """
    ),
    (
        "Add reliability to matches",
        """
        ALTER TABLE matches
        ADD COLUMN IF NOT EXISTS reliability FLOAT;
        """
    ),

    # phone normalisation
    (
        "Normalize 07XXXXXXXX phones to +2547XXXXXXXX",
        """
        UPDATE users
        SET phone = '+254' || SUBSTRING(phone FROM 2)
        WHERE phone ~ '^07' OR phone ~ '^01';
        """
    ),
    (
        "Normalize 2547XXXXXXXX phones (missing +)",
        """
        UPDATE users
        SET phone = '+' || phone
        WHERE phone ~ '^254' AND phone NOT LIKE '+%';
        """
    ),
]

print("Starting TrustGig DB migrations...\n")
for name, sql in migrations:
    try:
        cur.execute(sql)
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

cur.close()
conn.close()
print("\nMigration complete.")
