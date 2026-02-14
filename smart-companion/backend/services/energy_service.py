import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

class EnergyService:
    """
    Service for energy-adaptive scheduling.
    
    Tracks user energy levels throughout the day and provides
    recommendations for task timing based on energy patterns.
    """
    
    # Energy level labels
    ENERGY_LABELS = {
        (4, 5): "high",
        (3, 3): "medium", 
        (1, 2): "low"
    }
    
    def __init__(self):
        pass
    
    def parse_energy_log(self, energy_log_json: str) -> List[Dict[str, Any]]:
        """Parse energy log from JSON string."""
        try:
            return json.loads(energy_log_json) if energy_log_json else []
        except json.JSONDecodeError:
            return []
    
    def add_energy_entry(self, energy_log_json: str, energy_level: int) -> str:
        """
        Add a new energy entry to the log.
        
        Returns updated log as JSON string.
        """
        log = self.parse_energy_log(energy_log_json)
        
        now = datetime.now()
        entry = {
            "timestamp": now.isoformat(),
            "energy_level": energy_level,
            "hour": now.hour
        }
        
        log.append(entry)
        
        # Keep only last 100 entries to prevent bloat
        if len(log) > 100:
            log = log[-100:]
        
        return json.dumps(log)
    
    def calculate_hourly_averages(self, energy_log_json: str) -> Dict[int, float]:
        """
        Calculate average energy level for each hour of the day.
        
        Returns dict mapping hour (0-23) to average energy (1.0-5.0).
        """
        log = self.parse_energy_log(energy_log_json)
        
        if not log:
            # Return default moderate energy if no data
            return {h: 3.0 for h in range(24)}
        
        # Group by hour
        hourly_totals = defaultdict(list)
        for entry in log:
            hour = entry.get("hour", 12)
            level = entry.get("energy_level", 3)
            hourly_totals[hour].append(level)
        
        # Calculate averages
        hourly_averages = {}
        for hour in range(24):
            if hour in hourly_totals:
                hourly_averages[hour] = sum(hourly_totals[hour]) / len(hourly_totals[hour])
            else:
                # Interpolate or use default
                hourly_averages[hour] = 3.0
        
        return hourly_averages
    
    def identify_peak_hours(self, hourly_averages: Dict[int, float]) -> List[int]:
        """
        Identify hours with consistently high energy (4+).
        """
        return [hour for hour, avg in hourly_averages.items() if avg >= 4.0]
    
    def identify_low_energy_hours(self, hourly_averages: Dict[int, float]) -> List[int]:
        """
        Identify hours with consistently low energy (2 or below).
        """
        return [hour for hour, avg in hourly_averages.items() if avg <= 2.0]
    
    def get_energy_label(self, energy_level: float) -> str:
        """Get label for energy level."""
        if energy_level >= 4:
            return "high"
        elif energy_level >= 3:
            return "medium"
        else:
            return "low"
    
    def analyze_energy_patterns(self, energy_log_json: str) -> Dict[str, Any]:
        """
        Full energy analysis with patterns and recommendations.
        """
        hourly_averages = self.calculate_hourly_averages(energy_log_json)
        peak_hours = self.identify_peak_hours(hourly_averages)
        low_hours = self.identify_low_energy_hours(hourly_averages)
        
        # Create time block recommendations
        schedule = {
            "high_energy_tasks": {
                "hours": peak_hours if peak_hours else [9, 10, 11],
                "description": "Best for complex, demanding tasks"
            },
            "medium_energy_tasks": {
                "hours": [h for h in range(24) if h not in peak_hours and h not in low_hours],
                "description": "Good for routine tasks"
            },
            "low_energy_tasks": {
                "hours": low_hours if low_hours else [14, 15, 21, 22],
                "description": "Best for simple, automatic tasks"
            }
        }
        
        # Current recommendation
        current_hour = datetime.now().hour
        current_energy = hourly_averages.get(current_hour, 3.0)
        
        return {
            "hourly_averages": {str(k): round(v, 1) for k, v in hourly_averages.items()},
            "peak_hours": peak_hours,
            "low_energy_hours": low_hours,
            "recommended_schedule": schedule,
            "current_hour": current_hour,
            "current_predicted_energy": round(current_energy, 1),
            "current_energy_label": self.get_energy_label(current_energy)
        }
    
    def suggest_task_timing(
        self, 
        complexity_score: int, 
        hourly_averages: Dict[int, float]
    ) -> Dict[str, Any]:
        """
        Suggest optimal timing for a task based on its complexity.
        
        Args:
            complexity_score: Task complexity (1-10)
            hourly_averages: User's energy patterns
            
        Returns:
            Timing suggestion with hours and reasoning
        """
        peak_hours = self.identify_peak_hours(hourly_averages)
        low_hours = self.identify_low_energy_hours(hourly_averages)
        
        if complexity_score >= 7:
            # High complexity → need peak energy
            return {
                "complexity": "high",
                "suggested_hours": peak_hours if peak_hours else [9, 10, 11],
                "reason": "This task needs focus. Do it when energy is highest.",
                "window": "peak"
            }
        elif complexity_score >= 4:
            # Medium complexity → medium energy OK
            medium_hours = [h for h in range(24) if h not in peak_hours and h not in low_hours]
            return {
                "complexity": "medium",
                "suggested_hours": medium_hours if medium_hours else [9, 10, 14, 15],
                "reason": "This task is manageable. Any good energy time works.",
                "window": "medium"
            }
        else:
            # Low complexity → can do anytime, even low energy
            return {
                "complexity": "low",
                "suggested_hours": low_hours if low_hours else list(range(24)),
                "reason": "This is a simple task. Save your peak energy for harder things.",
                "window": "low"
            }


# Singleton instance
_energy_service = None

def get_energy_service() -> EnergyService:
    """Get or create the energy service singleton."""
    global _energy_service
    if _energy_service is None:
        _energy_service = EnergyService()
    return _energy_service
