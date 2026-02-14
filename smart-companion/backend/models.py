from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User model with encrypted sensitive fields."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # UI Preferences
    font_preference = Column(String(50), default="Lexend")
    high_contrast = Column(Boolean, default=False)
    
    # Encrypted JSON fields (stored as encrypted text)
    triggers = Column(Text, nullable=True)  # Encrypted JSON
    preferences = Column(Text, nullable=True)  # Encrypted JSON
    
    # Gamification
    streak_count = Column(Integer, default=0)
    badges = Column(Text, default="[]")  # JSON array of badge names
    
    # Energy tracking (JSON array of energy logs)
    energy_log = Column(Text, default="[]")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Task(Base):
    """Task model for tracking completed tasks."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    original_goal = Column(Text, nullable=False)
    micro_steps = Column(Text, nullable=False)  # JSON array
    completed_steps = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    complexity_score = Column(Integer, default=0)  # Cognitive load meter
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
