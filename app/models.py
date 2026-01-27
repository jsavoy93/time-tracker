"""SQLAlchemy models for categories and sessions."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from app.db import Base


class Category(Base):
    """Category model for grouping work sessions."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=soft deleted
    sort_order = Column(Integer, default=0, nullable=False)
    created_utc = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class Session(Base):
    """Session model for tracking work time."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    description = Column(Text, default="", nullable=False)
    start_utc = Column(String(50), nullable=False, index=True)
    end_utc = Column(String(50), nullable=True)
    created_utc = Column(String(50), nullable=False)
    updated_utc = Column(String(50), nullable=False)
    
    __table_args__ = (
        Index('idx_end_utc_is_null', 'end_utc'),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, category_id={self.category_id}, start={self.start_utc})>"
