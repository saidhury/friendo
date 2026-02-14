from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreate, UserPreferencesUpdate, UserResponse
from services.profile_service import get_profile_service

router = APIRouter(prefix="/users", tags=["users"])
profile_service = get_profile_service()


@router.post("/create", response_model=dict)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user profile.
    
    Sensitive data (triggers, preferences) is encrypted before storage.
    """
    try:
        user = profile_service.create_user(
            db=db,
            name=user_data.name,
            font_preference=user_data.font_preference,
            high_contrast=user_data.high_contrast,
            triggers=user_data.triggers,
            preferences=user_data.preferences
        )
        
        return profile_service.get_user(db, user.id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user profile by ID.
    
    Sensitive data is decrypted before returning.
    """
    user = profile_service.get_user(db, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/{user_id}/preferences", response_model=dict)
async def update_preferences(
    user_id: int, 
    updates: UserPreferencesUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update user preferences.
    
    All fields are optional - only provided fields are updated.
    Sensitive data is re-encrypted on update.
    """
    user = profile_service.update_preferences(
        db=db,
        user_id=user_id,
        font_preference=updates.font_preference,
        high_contrast=updates.high_contrast,
        triggers=updates.triggers,
        preferences=updates.preferences
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
