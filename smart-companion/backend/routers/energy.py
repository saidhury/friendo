from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import EnergyLogRequest, EnergyAnalysisResponse
from services.energy_service import get_energy_service
from services.profile_service import get_profile_service

router = APIRouter(prefix="/energy", tags=["energy"])
energy_service = get_energy_service()
profile_service = get_profile_service()


@router.post("/log")
async def log_energy(request: EnergyLogRequest, db: Session = Depends(get_db)):
    """
    Log current energy level (1-5).
    
    Stored with timestamp for pattern analysis.
    Used to build personalized energy schedule.
    """
    # Get user
    user = profile_service.get_user_model(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add energy entry
    updated_log = energy_service.add_energy_entry(
        user.energy_log,
        request.energy_level
    )
    
    # Save to database
    success = profile_service.update_energy_log(db, request.user_id, updated_log)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save energy log")
    
    return {
        "status": "logged",
        "energy_level": request.energy_level,
        "message": f"Energy level {request.energy_level} recorded!"
    }


@router.get("/analysis/{user_id}")
async def get_energy_analysis(user_id: int, db: Session = Depends(get_db)):
    """
    Get energy pattern analysis for user.
    
    Returns:
    - Hourly energy averages
    - Peak energy hours
    - Low energy hours  
    - Recommended schedule by task complexity
    """
    # Get user
    user = profile_service.get_user_model(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Analyze energy patterns
    analysis = energy_service.analyze_energy_patterns(user.energy_log)
    
    return {
        "user_id": user_id,
        **analysis
    }


@router.get("/suggestion/{user_id}")
async def get_current_suggestion(user_id: int, db: Session = Depends(get_db)):
    """
    Get current energy-based suggestion.
    
    Based on current time and user's historical patterns,
    suggests what type of task to work on now.
    """
    # Get user
    user = profile_service.get_user_model(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current analysis
    analysis = energy_service.analyze_energy_patterns(user.energy_log)
    
    current_energy = analysis["current_predicted_energy"]
    current_label = analysis["current_energy_label"]
    
    # Generate suggestion
    if current_label == "high":
        suggestion = "Great energy right now! Perfect time for challenging tasks."
        recommended_complexity = "high"
    elif current_label == "medium":
        suggestion = "Good energy level. Handle your routine tasks now."
        recommended_complexity = "medium"
    else:
        suggestion = "Lower energy detected. Stick to simple, easy tasks."
        recommended_complexity = "low"
    
    return {
        "user_id": user_id,
        "current_hour": analysis["current_hour"],
        "predicted_energy": current_energy,
        "energy_label": current_label,
        "suggestion": suggestion,
        "recommended_task_complexity": recommended_complexity,
        "peak_hours_today": analysis["peak_hours"],
        "low_energy_hours": analysis["low_energy_hours"]
    }
