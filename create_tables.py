"""
Creates all DB tables defined in models.py using SQLAlchemy ORM.
Run once to set up the database schema.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "trustgig"))

from database import Base, engine
import models  # registers all table classes with Base

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done. Tables created:")

import psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
for row in cur.fetchall():
    print(f"  - {row[0]}")
conn.close()
