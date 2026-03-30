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
    # ✅ Fix #3 — add assigned_freelancer_id to jobs table
    (
        "Add assigned_freelancer_id to jobs",
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS assigned_freelancer_id INTEGER
        REFERENCES users(id) ON DELETE SET NULL;
        """
    ),

    # ✅ Fix #12 — drop similarity_score (was always 0.0, caused the original 500 error)
    # Safe: check if column exists first
    (
        "Drop similarity_score from matches",
        """
        ALTER TABLE matches
        DROP COLUMN IF EXISTS similarity_score;
        """
    ),

    # ✅ Add created_at to jobs if missing
    (
        "Add created_at to jobs",
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
        """
    ),

    # ✅ Normalize existing phone numbers to +2547XXXXXXXX format
    # Handles 07XXXXXXXX stored without country code
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
        print(f"  ✅ {name}")
    except Exception as e:
        print(f"  ❌ {name}: {e}")

cur.close()
conn.close()
print("\nMigration complete.")
