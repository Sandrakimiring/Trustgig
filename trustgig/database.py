from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
-- Active: 1767170877878@@127.0.0.1@5432@Trustgig
from sqlachemy import craete_engine
from sqlachemy.orm import sessionmaker, declarative_base

DB_USER = "postgres"
DB_PASS = "12345678"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Trustgig"


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

# SessionLocal will be used in endpoints
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()