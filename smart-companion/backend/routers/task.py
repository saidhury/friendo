import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Task
from schemas import (
    TaskDecomposeRequest, 
    TaskDecomposeResponse, 
    TaskCompleteRequest,
    TaskCompleteResponse,
    MicroStep
)
from services.llm_service import get_llm_service
from services.energy_service import get_energy_service
from services.gamification_service import get_gamification_service
from services.profile_service import get_profile_service

router = APIRouter(prefix="/tasks", tags=["tasks"])
llm_service = get_llm_service()
energy_service = get_energy_service()
gamification_service = get_gamification_service()
profile_service = get_profile_service()


@router.post("/decompose", response_model=TaskDecomposeResponse)
async def decompose_task(request: TaskDecomposeRequest, db: Session = Depends(get_db)):
    """
    Decompose a goal into micro-steps.
    
    1. PII is masked before any LLM processing
    2. Goal is broken into 2-5 minute MicroWins
    3. Returns first 5 steps immediately
    4. Includes complexity score and energy-based timing suggestion
    """
    # Verify user exists
    user = profile_service.get_user_model(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Decompose the task
        result = await llm_service.decompose_task(request.goal)
        
        # Get energy-based suggestion
        hourly_averages = energy_service.calculate_hourly_averages(user.energy_log)
        timing_suggestion = energy_service.suggest_task_timing(
            result["complexity_score"],
            hourly_averages
        )
        
        # Create task record
        task = Task(
            user_id=request.user_id,
            original_goal=request.goal,
            micro_steps=json.dumps(result["all_steps"]),
            completed_steps=0,
            total_steps=result["total_steps"],
            complexity_score=result["complexity_score"],
            is_completed=False
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Format response
        micro_steps = [
            MicroStep(
                step_number=step["step_number"],
                action=step["action"],
                estimated_minutes=step.get("estimated_minutes", 3)
            )
            for step in result["steps"]
        ]
        
        return TaskDecomposeResponse(
            task_id=task.id,
            goal=request.goal,
            micro_steps=micro_steps,
            total_steps=result["total_steps"],
            complexity_score=result["complexity_score"],
            suggested_energy_window=timing_suggestion["reason"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decompose task: {str(e)}")


@router.post("/complete", response_model=TaskCompleteResponse)
async def complete_task_step(request: TaskCompleteRequest, db: Session = Depends(get_db)):
    """
    Mark a task step as completed.
    
    When all steps are done:
    - Streak is incremented
    - Badges are checked and awarded
    - Celebration message is returned
    """
    # Get task
    task = db.query(Task).filter(Task.id == request.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="Task belongs to different user")
    
    if task.is_completed:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Get user
    user = profile_service.get_user_model(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Increment completed steps
    task.completed_steps += 1
    
    new_streak = user.streak_count
    badges_earned = []
    celebration_message = gamification_service.get_celebration_message(task.completed_steps)
    
    # Check if task is fully completed
    if task.completed_steps >= task.total_steps:
        task.is_completed = True
        task.completed_at = datetime.utcnow()
        
        # Process gamification
        gamification_result = gamification_service.process_task_completion(
            user.streak_count,
            user.badges
        )
        
        new_streak = gamification_result["new_streak"]
        badges_earned = gamification_result["badges_earned"]
        celebration_message = gamification_result["celebration_message"]
        
        if gamification_result["badge_messages"]:
            celebration_message += " " + " ".join(gamification_result["badge_messages"])
        
        # Update user
        profile_service.update_streak(
            db, 
            request.user_id, 
            new_streak, 
            gamification_result["badges_json"]
        )
    
    db.commit()
    
    return TaskCompleteResponse(
        task_id=task.id,
        completed_steps=task.completed_steps,
        total_steps=task.total_steps,
        is_fully_completed=task.is_completed,
        new_streak=new_streak,
        badges_earned=badges_earned,
        celebration_message=celebration_message
    )


@router.get("/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get task details by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    steps = json.loads(task.micro_steps)
    
    return {
        "id": task.id,
        "user_id": task.user_id,
        "goal": task.original_goal,
        "micro_steps": steps,
        "completed_steps": task.completed_steps,
        "total_steps": task.total_steps,
        "complexity_score": task.complexity_score,
        "is_completed": task.is_completed,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


@router.get("/user/{user_id}/active")
async def get_active_task(user_id: int, db: Session = Depends(get_db)):
    """Get user's current active (incomplete) task."""
    task = db.query(Task).filter(
        Task.user_id == user_id,
        Task.is_completed == False
    ).order_by(Task.created_at.desc()).first()
    
    if not task:
        return {"active_task": None}
    
    steps = json.loads(task.micro_steps)
    current_step_index = task.completed_steps
    
    return {
        "active_task": {
            "id": task.id,
            "goal": task.original_goal,
            "micro_steps": steps,
            "completed_steps": task.completed_steps,
            "total_steps": task.total_steps,
            "current_step": steps[current_step_index] if current_step_index < len(steps) else None,
            "complexity_score": task.complexity_score
        }
    }
