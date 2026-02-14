import json
from typing import List, Dict, Any, Tuple

class GamificationService:
    """
    Service for gamification features.
    
    Manages streaks, badges, and celebration messages
    to maintain user motivation.
    """
    
    # Badge definitions
    BADGES = {
        "bronze": {
            "name": "Bronze Achiever",
            "icon": "🥉",
            "streak_required": 5,
            "message": "You earned Bronze! 5 tasks completed!"
        },
        "silver": {
            "name": "Silver Star",
            "icon": "🥈", 
            "streak_required": 10,
            "message": "Silver unlocked! 10 tasks done!"
        },
        "gold": {
            "name": "Gold Champion",
            "icon": "🥇",
            "streak_required": 20,
            "message": "GOLD! You're unstoppable! 20 tasks!"
        },
        "diamond": {
            "name": "Diamond Legend",
            "icon": "💎",
            "streak_required": 50,
            "message": "DIAMOND! Legendary achievement! 50 tasks!"
        }
    }
    
    # Celebration messages for task completion
    CELEBRATION_MESSAGES = [
        "Great job! One step done! 🎉",
        "You did it! Keep going! ⭐",
        "Amazing progress! 🚀",
        "That's the way! 💪",
        "Fantastic work! 🌟",
        "You're on fire! 🔥",
        "Excellent! Moving forward! ✨",
        "Wonderful! Keep the momentum! 🎯"
    ]
    
    # Messages for completing full tasks
    TASK_COMPLETE_MESSAGES = [
        "🎉 Task COMPLETE! You're amazing!",
        "🏆 All steps done! Celebrate this win!",
        "⭐ Full task finished! You rock!",
        "🎊 Mission accomplished! Great work!",
        "🌟 Task crushed! You're unstoppable!"
    ]
    
    def __init__(self):
        pass
    
    def parse_badges(self, badges_json: str) -> List[str]:
        """Parse badges from JSON string."""
        try:
            return json.loads(badges_json) if badges_json else []
        except json.JSONDecodeError:
            return []
    
    def badges_to_json(self, badges: List[str]) -> str:
        """Convert badges list to JSON string."""
        return json.dumps(badges)
    
    def increment_streak(self, current_streak: int) -> int:
        """Increment streak count."""
        return current_streak + 1
    
    def check_new_badges(
        self, 
        new_streak: int, 
        existing_badges: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Check if new badges have been earned.
        
        Returns:
            Tuple of (updated_badges_list, newly_earned_badges)
        """
        new_badges = []
        all_badges = existing_badges.copy()
        
        for badge_id, badge_info in self.BADGES.items():
            if badge_id not in existing_badges:
                if new_streak >= badge_info["streak_required"]:
                    all_badges.append(badge_id)
                    new_badges.append(badge_id)
        
        return all_badges, new_badges
    
    def get_badge_info(self, badge_id: str) -> Dict[str, Any]:
        """Get full badge information."""
        return self.BADGES.get(badge_id, {
            "name": "Unknown",
            "icon": "❓",
            "streak_required": 0,
            "message": ""
        })
    
    def get_celebration_message(self, step_number: int) -> str:
        """Get a celebration message for completing a step."""
        index = (step_number - 1) % len(self.CELEBRATION_MESSAGES)
        return self.CELEBRATION_MESSAGES[index]
    
    def get_task_complete_message(self, streak: int) -> str:
        """Get a message for completing a full task."""
        index = streak % len(self.TASK_COMPLETE_MESSAGES)
        return self.TASK_COMPLETE_MESSAGES[index]
    
    def get_badge_display(self, badges: List[str]) -> List[Dict[str, str]]:
        """Get display information for all badges."""
        display = []
        for badge_id in badges:
            info = self.get_badge_info(badge_id)
            display.append({
                "id": badge_id,
                "name": info["name"],
                "icon": info["icon"]
            })
        return display
    
    def get_next_badge_progress(
        self, 
        current_streak: int, 
        existing_badges: List[str]
    ) -> Dict[str, Any]:
        """
        Get progress toward the next badge.
        """
        # Find next unearned badge
        for badge_id, badge_info in sorted(
            self.BADGES.items(), 
            key=lambda x: x[1]["streak_required"]
        ):
            if badge_id not in existing_badges:
                remaining = badge_info["streak_required"] - current_streak
                return {
                    "next_badge": badge_id,
                    "badge_name": badge_info["name"],
                    "badge_icon": badge_info["icon"],
                    "tasks_remaining": max(0, remaining),
                    "progress_percent": min(100, int(
                        (current_streak / badge_info["streak_required"]) * 100
                    ))
                }
        
        # All badges earned
        return {
            "next_badge": None,
            "badge_name": "All Badges Earned!",
            "badge_icon": "🏆",
            "tasks_remaining": 0,
            "progress_percent": 100
        }
    
    def process_task_completion(
        self,
        current_streak: int,
        existing_badges_json: str
    ) -> Dict[str, Any]:
        """
        Process a full task completion.
        
        Returns all gamification updates in one call.
        """
        # Increment streak
        new_streak = self.increment_streak(current_streak)
        
        # Check badges
        existing_badges = self.parse_badges(existing_badges_json)
        all_badges, new_badges = self.check_new_badges(new_streak, existing_badges)
        
        # Get messages
        celebration = self.get_task_complete_message(new_streak)
        
        # Get badge messages
        badge_messages = []
        for badge_id in new_badges:
            info = self.get_badge_info(badge_id)
            badge_messages.append(info["message"])
        
        # Get next badge progress
        next_progress = self.get_next_badge_progress(new_streak, all_badges)
        
        return {
            "new_streak": new_streak,
            "badges_earned": new_badges,
            "all_badges": all_badges,
            "badges_json": self.badges_to_json(all_badges),
            "celebration_message": celebration,
            "badge_messages": badge_messages,
            "next_badge_progress": next_progress,
            "should_celebrate": True,
            "show_confetti": len(new_badges) > 0 or new_streak % 5 == 0
        }


# Singleton instance
_gamification_service = None

def get_gamification_service() -> GamificationService:
    """Get or create the gamification service singleton."""
    global _gamification_service
    if _gamification_service is None:
        _gamification_service = GamificationService()
    return _gamification_service
