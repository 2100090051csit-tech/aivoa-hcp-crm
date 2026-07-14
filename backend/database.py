import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration: defaults to SQLite for easy local setup,
# but can connect to PostgreSQL/MySQL via DATABASE_URL environment variable.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm.db")

# For SQLite, we need connect_args={"check_same_thread": False}
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
