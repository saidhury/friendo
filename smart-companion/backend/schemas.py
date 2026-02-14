from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# ==================== User Schemas ====================

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str = Field(..., min_length=1, max_length=100)
    font_preference: str = Field(default="Lexend")
    high_contrast: bool = Field(default=False)
    triggers: Optional[List[str]] = Field(default=[])
    preferences: Optional[dict] = Field(default={})

class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    font_preference: Optional[str] = None
    high_contrast: Optional[bool] = None
    triggers: Optional[List[str]] = None
    preferences: Optional[dict] = None

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    name: str
    font_preference: str
    high_contrast: bool
    triggers: List[str]
    preferences: dict
    streak_count: int
    badges: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== Task Schemas ====================

class TaskDecomposeRequest(BaseModel):
    """Schema for task decomposition request."""
    user_id: int
    goal: str = Field(..., min_length=1, max_length=500)

class MicroStep(BaseModel):
    """Schema for a single micro-step."""
    step_number: int
    action: str
    estimated_minutes: int = Field(default=3, ge=1, le=5)

class TaskDecomposeResponse(BaseModel):
    """Schema for task decomposition response."""
    task_id: int
    goal: str
    micro_steps: List[MicroStep]
    total_steps: int
    complexity_score: int
    suggested_energy_window: str

class TaskCompleteRequest(BaseModel):
    """Schema for completing a task step."""
    task_id: int
    user_id: int

class TaskCompleteResponse(BaseModel):
    """Schema for task completion response."""
    task_id: int
    completed_steps: int
    total_steps: int
    is_fully_completed: bool
    new_streak: int
    badges_earned: List[str]
    celebration_message: str

# ==================== Energy Schemas ====================

class EnergyLogRequest(BaseModel):
    """Schema for logging energy level."""
    user_id: int
    energy_level: int = Field(..., ge=1, le=5)

class EnergyLogEntry(BaseModel):
    """Schema for a single energy log entry."""
    timestamp: str
    energy_level: int
    hour: int

class EnergyAnalysisResponse(BaseModel):
    """Schema for energy analysis response."""
    user_id: int
    hourly_averages: dict  # hour -> average energy
    peak_hours: List[int]
    low_energy_hours: List[int]
    recommended_schedule: dict

class TaskSuggestion(BaseModel):
    """Schema for task timing suggestion."""
    complexity: str
    suggested_hours: List[int]
    reason: str
