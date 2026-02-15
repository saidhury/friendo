import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from config import get_settings
from services.pii_masking_service import get_pii_masking_service

# Try to import google-genai SDK
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class LLMService:
    """Service for LLM-based task decomposition with privacy protection."""
    
    SYSTEM_PROMPT = """You are a neuro-inclusive executive function assistant.
Break the goal into very small MicroWins.

Rules:
- 2-5 minute tasks only
- 1 action per step
- Simple language
- No dense text
- No long explanations
- Return JSON array only
- Max 10 steps total
- Return first 5 immediately

Return ONLY a JSON array in this exact format:
[
  {"step_number": 1, "action": "First simple action", "estimated_minutes": 3},
  {"step_number": 2, "action": "Second simple action", "estimated_minutes": 2}
]

No other text, just the JSON array."""

    def __init__(self):
        self.settings = get_settings()
        self.pii_service = get_pii_masking_service()
    
    def _calculate_complexity(self, goal: str, steps: List[Dict]) -> int:
        """
        Calculate cognitive load score (1-10) based on:
        - Word count in goal
        - Number of steps
        - Average step length
        """
        word_count = len(goal.split())
        step_count = len(steps)
        avg_step_words = sum(len(s.get('action', '').split()) for s in steps) / max(step_count, 1)
        
        # Simple scoring algorithm
        complexity = min(10, max(1, 
            (word_count // 5) + 
            (step_count // 2) + 
            int(avg_step_words / 3)
        ))
        
        return complexity
    
    def _generate_fallback_steps(self, goal: str) -> List[Dict[str, Any]]:
        """
        Generate simple fallback micro-steps when LLM is unavailable.
        Uses rule-based decomposition for common task patterns.
        """
        goal_lower = goal.lower()
        
        # Common task patterns with pre-defined micro-steps
        if any(word in goal_lower for word in ['clean', 'tidy', 'organize']):
            return [
                {"step_number": 1, "action": "Pick one small area to start", "estimated_minutes": 2},
                {"step_number": 2, "action": "Gather items that don't belong", "estimated_minutes": 3},
                {"step_number": 3, "action": "Put away 5 items", "estimated_minutes": 3},
                {"step_number": 4, "action": "Wipe down one surface", "estimated_minutes": 2},
                {"step_number": 5, "action": "Take a quick look and celebrate", "estimated_minutes": 1},
            ]
        
        if any(word in goal_lower for word in ['write', 'email', 'message', 'report']):
            return [
                {"step_number": 1, "action": "Open where you'll write", "estimated_minutes": 1},
                {"step_number": 2, "action": "Write just the first sentence", "estimated_minutes": 3},
                {"step_number": 3, "action": "Add one more idea", "estimated_minutes": 3},
                {"step_number": 4, "action": "Read it once quickly", "estimated_minutes": 2},
                {"step_number": 5, "action": "Click send or save", "estimated_minutes": 1},
            ]
        
        if any(word in goal_lower for word in ['exercise', 'workout', 'run', 'walk']):
            return [
                {"step_number": 1, "action": "Put on your shoes", "estimated_minutes": 2},
                {"step_number": 2, "action": "Step outside or to your spot", "estimated_minutes": 1},
                {"step_number": 3, "action": "Do just 2 minutes of movement", "estimated_minutes": 2},
                {"step_number": 4, "action": "Take 3 deep breaths", "estimated_minutes": 1},
                {"step_number": 5, "action": "Do 2 more minutes if you want", "estimated_minutes": 2},
            ]
        
        if any(word in goal_lower for word in ['study', 'learn', 'read', 'homework']):
            return [
                {"step_number": 1, "action": "Get your materials ready", "estimated_minutes": 2},
                {"step_number": 2, "action": "Read just one paragraph", "estimated_minutes": 3},
                {"step_number": 3, "action": "Write one key point", "estimated_minutes": 2},
                {"step_number": 4, "action": "Take a tiny stretch break", "estimated_minutes": 1},
                {"step_number": 5, "action": "Read one more paragraph", "estimated_minutes": 3},
            ]
        
        if any(word in goal_lower for word in ['cook', 'meal', 'food', 'eat']):
            return [
                {"step_number": 1, "action": "Decide what to make", "estimated_minutes": 2},
                {"step_number": 2, "action": "Get out one ingredient", "estimated_minutes": 1},
                {"step_number": 3, "action": "Get out the rest", "estimated_minutes": 2},
                {"step_number": 4, "action": "Start the first step of cooking", "estimated_minutes": 3},
                {"step_number": 5, "action": "Set a timer if needed", "estimated_minutes": 1},
            ]
        
        # Generic fallback for any task
        words = goal.split()[:3]
        task_hint = ' '.join(words) if words else 'this task'
        
        return [
            {"step_number": 1, "action": f"Think about what you need for {task_hint}", "estimated_minutes": 2},
            {"step_number": 2, "action": "Gather one thing you'll need", "estimated_minutes": 2},
            {"step_number": 3, "action": "Start the very first action", "estimated_minutes": 3},
            {"step_number": 4, "action": "Do just the next small piece", "estimated_minutes": 3},
            {"step_number": 5, "action": "Check your progress and continue", "estimated_minutes": 2},
        ]
    
    async def decompose_task(self, goal: str) -> Dict[str, Any]:
        """
        Decompose a goal into micro-steps.
        
        1. Masks PII before any LLM call
        2. Calls LLM if configured, otherwise uses fallback
        3. Returns structured micro-steps with complexity score
        """
        # Step 1: Mask PII
        masked_goal, pii_map = self.pii_service.mask_text(goal)
        
        steps = []
        
        # Step 2: Try Gemini first, then OpenAI-compatible, then fallback
        if self.settings.GEMINI_API_KEY:
            try:
                steps = await self._call_gemini(masked_goal)
            except Exception as e:
                print(f"Gemini call failed: {e}, trying fallback")
                steps = []
        elif self.settings.LLM_API_URL and self.settings.LLM_API_KEY:
            try:
                steps = await self._call_llm(masked_goal)
            except Exception as e:
                print(f"LLM call failed: {e}, using fallback")
                steps = []
        
        # Step 3: Use fallback if LLM not available or failed
        if not steps:
            steps = self._generate_fallback_steps(masked_goal)
        
        # Step 4: Calculate complexity
        complexity = self._calculate_complexity(goal, steps)
        
        # Step 5: Unmask any PII in steps (shouldn't be any, but safety check)
        for step in steps:
            step['action'] = self.pii_service.unmask_text(step['action'], pii_map)
        
        return {
            "steps": steps[:5],  # Return first 5 immediately
            "total_steps": len(steps),
            "all_steps": steps,
            "complexity_score": complexity
        }
    
    async def _call_gemini(self, goal: str) -> List[Dict[str, Any]]:
        """Call Gemini API using the official SDK."""
        if not GENAI_AVAILABLE:
            print("google-genai SDK not installed, using fallback")
            return []
        
        prompt = f"""{self.SYSTEM_PROMPT}

Break down this goal: {goal}"""
        
        try:
            # Create client with API key
            client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            
            # Run sync call in executor to not block async loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.settings.GEMINI_MODEL,
                    contents=prompt
                )
            )
            
            # Extract text from response
            content = response.text
            
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"Gemini SDK error: {e}")
        
        return []

    async def _call_llm(self, goal: str) -> List[Dict[str, Any]]:
        """Call external OpenAI-compatible LLM API with masked goal."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.settings.LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Break down this goal: {goal}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse JSON from response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return []


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
