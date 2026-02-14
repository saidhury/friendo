import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from models import User
from services.encryption_service import get_encryption_service
from services.gamification_service import get_gamification_service

class ProfileService:
    """
    Service for managing user profiles with encryption.
    
    Handles creation, retrieval, and updates of user profiles
    while ensuring sensitive data is encrypted at rest.
    """
    
    def __init__(self):
        self.encryption = get_encryption_service()
        self.gamification = get_gamification_service()
    
    def create_user(
        self,
        db: Session,
        name: str,
        font_preference: str = "Lexend",
        high_contrast: bool = False,
        triggers: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create a new user with encrypted sensitive fields.
        """
        # Encrypt sensitive data
        encrypted_triggers = self.encryption.encrypt_json(triggers or [])
        encrypted_preferences = self.encryption.encrypt_json(preferences or {})
        
        user = User(
            name=name,
            font_preference=font_preference,
            high_contrast=high_contrast,
            triggers=encrypted_triggers,
            preferences=encrypted_preferences,
            streak_count=0,
            badges="[]",
            energy_log="[]"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID with decrypted sensitive fields.
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
        
        return self._user_to_dict(user)
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user model to dictionary with decryption."""
        return {
            "id": user.id,
            "name": user.name,
            "font_preference": user.font_preference,
            "high_contrast": user.high_contrast,
            "triggers": self.encryption.decrypt_json(user.triggers, []),
            "preferences": self.encryption.decrypt_json(user.preferences, {}),
            "streak_count": user.streak_count,
            "badges": self.gamification.parse_badges(user.badges),
            "energy_log": json.loads(user.energy_log) if user.energy_log else [],
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    def update_preferences(
        self,
        db: Session,
        user_id: int,
        font_preference: Optional[str] = None,
        high_contrast: Optional[bool] = None,
        triggers: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user preferences with encryption.
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
        
        if font_preference is not None:
            user.font_preference = font_preference
        
        if high_contrast is not None:
            user.high_contrast = high_contrast
        
        if triggers is not None:
            user.triggers = self.encryption.encrypt_json(triggers)
        
        if preferences is not None:
            user.preferences = self.encryption.encrypt_json(preferences)
        
        db.commit()
        db.refresh(user)
        
        return self._user_to_dict(user)
    
    def update_streak(
        self,
        db: Session,
        user_id: int,
        new_streak: int,
        new_badges_json: str
    ) -> bool:
        """Update user's streak and badges."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False
        
        user.streak_count = new_streak
        user.badges = new_badges_json
        
        db.commit()
        return True
    
    def update_energy_log(
        self,
        db: Session,
        user_id: int,
        energy_log_json: str
    ) -> bool:
        """Update user's energy log."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return False
        
        user.energy_log = energy_log_json
        
        db.commit()
        return True
    
    def get_user_model(self, db: Session, user_id: int) -> Optional[User]:
        """Get raw user model (for internal use)."""
        return db.query(User).filter(User.id == user_id).first()


# Singleton instance
_profile_service = None

def get_profile_service() -> ProfileService:
    """Get or create the profile service singleton."""
    global _profile_service
    if _profile_service is None:
        _profile_service = ProfileService()
    return _profile_service
