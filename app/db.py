"""Database initialization and session management."""
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed default data."""
    Base.metadata.create_all(bind=engine)
    
    # Seed default categories if none exist
    db = SessionLocal()
    try:
        from app.models import Category
        existing = db.query(Category).count()
        if existing == 0:
            defaults = [
                {"name": "Coding", "sort_order": 10},
                {"name": "Meetings", "sort_order": 20},
                {"name": "Support", "sort_order": 30},
                {"name": "Planning", "sort_order": 40},
                {"name": "Admin", "sort_order": 50},
            ]
            for item in defaults:
                cat = Category(
                    name=item["name"],
                    sort_order=item["sort_order"],
                    created_utc=datetime.utcnow().isoformat() + "Z",
                )
                db.add(cat)
            db.commit()
    finally:
        db.close()
