import os, sys
from sqlalchemy import create_engine
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from models import Base
# Also import ML models so they get dropped/created too
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trustgig.models import Base as MLBase

DB_URL = 'postgresql://trustgig_db_user:uYRr6hetpwfHfoxsmdFGn7knlS5k5xy6@dpg-d6qr4a5m5p6s73e8mpg0-a.oregon-postgres.render.com/trustgig_db?sslmode=require'

print(f"Connecting to live production database at Render...")
engine = create_engine(DB_URL)

try:
    print("Dropping all existing Main Backend tables...")
    Base.metadata.drop_all(bind=engine)
    print("Dropping all ML matching tables...")
    MLBase.metadata.drop_all(bind=engine)
    
    print("Recreating fresh Main Backend tables...")
    Base.metadata.create_all(bind=engine)
    print("Recreating fresh ML matching tables...")
    MLBase.metadata.create_all(bind=engine)
    
    print("Database wiped and rebuilt successfully! It is completely clean.")
except Exception as e:
    print(f"Error: {e}")
