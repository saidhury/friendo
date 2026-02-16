import json
import re
import asyncio
import time
import base64
import httpx
from typing import List, Dict, Any, Optional, Tuple
from config import get_settings
from services.pii_masking_service import get_pii_masking_service

# Import logger for LLM calls
try:
    from api_logger import log_to_file
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    def log_to_file(entry: str):
        pass  # No-op if logger not available

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
- Minimum 2 steps, maximum 10 steps
- Use ONLY as many steps as truly needed for the task
- Simple tasks need fewer steps (2-4), complex tasks need more (5-10)
- Don't pad with unnecessary steps

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
        Returns appropriate number of steps based on task complexity.
        """
        goal_lower = goal.lower()
        word_count = len(goal.split())
        
        # Common task patterns with pre-defined micro-steps
        # Simple tasks (short goals) get fewer steps
        if any(word in goal_lower for word in ['clean', 'tidy', 'organize']):
            steps = [
                {"step_number": 1, "action": "Pick one small area to start", "estimated_minutes": 2},
                {"step_number": 2, "action": "Gather items that don't belong", "estimated_minutes": 3},
                {"step_number": 3, "action": "Put away 5 items", "estimated_minutes": 3},
            ]
            # Add more steps for complex cleaning tasks
            if word_count > 5 or 'room' in goal_lower or 'house' in goal_lower:
                steps.extend([
                    {"step_number": 4, "action": "Wipe down one surface", "estimated_minutes": 2},
                    {"step_number": 5, "action": "Take a quick look and celebrate", "estimated_minutes": 1},
                ])
            return steps
        
        if any(word in goal_lower for word in ['write', 'email', 'message']):
            # Short messages need fewer steps
            if 'quick' in goal_lower or 'short' in goal_lower or word_count <= 4:
                return [
                    {"step_number": 1, "action": "Open where you'll write", "estimated_minutes": 1},
                    {"step_number": 2, "action": "Write your message", "estimated_minutes": 3},
                    {"step_number": 3, "action": "Click send", "estimated_minutes": 1},
                ]
            return [
                {"step_number": 1, "action": "Open where you'll write", "estimated_minutes": 1},
                {"step_number": 2, "action": "Write just the first sentence", "estimated_minutes": 3},
                {"step_number": 3, "action": "Add one more idea", "estimated_minutes": 3},
                {"step_number": 4, "action": "Read it once quickly", "estimated_minutes": 2},
                {"step_number": 5, "action": "Click send or save", "estimated_minutes": 1},
            ]
        
        if any(word in goal_lower for word in ['report', 'document', 'essay']):
            return [
                {"step_number": 1, "action": "Open your document", "estimated_minutes": 1},
                {"step_number": 2, "action": "Write a simple outline", "estimated_minutes": 3},
                {"step_number": 3, "action": "Write the first paragraph", "estimated_minutes": 4},
                {"step_number": 4, "action": "Write the next section", "estimated_minutes": 4},
                {"step_number": 5, "action": "Take a short break", "estimated_minutes": 2},
                {"step_number": 6, "action": "Continue writing", "estimated_minutes": 4},
                {"step_number": 7, "action": "Review what you wrote", "estimated_minutes": 3},
                {"step_number": 8, "action": "Save your work", "estimated_minutes": 1},
            ]
        
        if any(word in goal_lower for word in ['exercise', 'workout', 'run', 'walk']):
            # Quick exercise = fewer steps
            if 'quick' in goal_lower or word_count <= 3:
                return [
                    {"step_number": 1, "action": "Put on your shoes", "estimated_minutes": 2},
                    {"step_number": 2, "action": "Do 5 minutes of movement", "estimated_minutes": 5},
                ]
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
            # Simple eating task
            if 'snack' in goal_lower or 'eat' in goal_lower:
                return [
                    {"step_number": 1, "action": "Go to the kitchen", "estimated_minutes": 1},
                    {"step_number": 2, "action": "Get your food ready", "estimated_minutes": 2},
                ]
            return [
                {"step_number": 1, "action": "Decide what to make", "estimated_minutes": 2},
                {"step_number": 2, "action": "Get out one ingredient", "estimated_minutes": 1},
                {"step_number": 3, "action": "Get out the rest", "estimated_minutes": 2},
                {"step_number": 4, "action": "Start the first step of cooking", "estimated_minutes": 3},
                {"step_number": 5, "action": "Set a timer if needed", "estimated_minutes": 1},
            ]
        
        # Generic fallback - scale steps based on goal complexity
        words = goal.split()[:3]
        task_hint = ' '.join(words) if words else 'this task'
        
        # Very simple goals (1-3 words) get minimal steps
        if word_count <= 3:
            return [
                {"step_number": 1, "action": f"Start {task_hint}", "estimated_minutes": 2},
                {"step_number": 2, "action": "Complete the task", "estimated_minutes": 3},
            ]
        
        # Medium complexity (4-7 words)
        if word_count <= 7:
            return [
                {"step_number": 1, "action": f"Think about what you need for {task_hint}", "estimated_minutes": 2},
                {"step_number": 2, "action": "Gather one thing you'll need", "estimated_minutes": 2},
                {"step_number": 3, "action": "Start the very first action", "estimated_minutes": 3},
            ]
        
        # Complex goals (8+ words) get more steps
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
        
        # Ensure we have at least 2 and at most 10 steps
        steps = steps[:10] if len(steps) > 10 else steps
        
        return {
            "steps": steps,  # Return all steps (LLM decides count based on task)
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
        
        start_time = time.time()
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
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the LLM call
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_entry = [
                    "[LLM CALL] Gemini API",
                    f"Model: {self.settings.GEMINI_MODEL}",
                    f"Duration: {duration_ms:.2f}ms",
                    f"Prompt:\n{prompt}",
                    f"Response:\n{content}"
                ]
                log_to_file("\n".join(log_entry))
                print(f"📝 Logged LLM call: Gemini ({duration_ms:.2f}ms)")
            
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            print(f"Gemini SDK error: {e}")
            
            # Log the error
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_entry = [
                    "[LLM CALL ERROR] Gemini API",
                    f"Model: {self.settings.GEMINI_MODEL}",
                    f"Duration: {duration_ms:.2f}ms",
                    f"Prompt:\n{prompt}",
                    f"Error: {str(e)}"
                ]
                log_to_file("\n".join(log_entry))
        
        return []

    async def _call_llm(self, goal: str) -> List[Dict[str, Any]]:
        """Call external OpenAI-compatible LLM API with masked goal."""
        request_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Break down this goal: {goal}"}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.settings.LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=request_payload
            )
            
            duration_ms = (time.time() - start_time) * 1000
            response_text = response.text
            
            # Log the LLM call
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_entry = [
                    "[LLM CALL] OpenAI-compatible API",
                    f"URL: {self.settings.LLM_API_URL}",
                    f"Status: {response.status_code}",
                    f"Duration: {duration_ms:.2f}ms",
                    f"Request:\n{json.dumps(request_payload, indent=2)}",
                    f"Response:\n{response_text}"
                ]
                log_to_file("\n".join(log_entry))
                print(f"📝 Logged LLM call: OpenAI-compatible ({duration_ms:.2f}ms)")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse JSON from response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return []


    # ==================== Image Context Methods ====================
    
    IMAGE_ANALYSIS_PROMPT = """You are analyzing a user's task to determine if a photo would help provide better context.

Consider if the task involves:
- Physical spaces (cleaning, organizing, decorating)
- Visual items (fixing something, identifying objects)
- Layouts or arrangements
- Anything where seeing the actual situation would help create better steps

Respond with ONLY a JSON object in this exact format:
{
  "needs_image": true or false,
  "image_prompt": "A SHORT, friendly question (max 10 words) asking for a photo. No emojis. Example: 'Can I see your desk?' or 'Show me what needs cleaning?'",
  "image_type": "brief description of what kind of image would help (only if needs_image is true)"
}

Keep image_prompt VERY short - it should be a simple question, not an explanation.

Examples:
- "Clean my room" -> needs_image: true, image_prompt: "Can I see your room?"
- "Write an email" -> needs_image: false
- "Organize my desk" -> needs_image: true, image_prompt: "Show me your desk?"
- "Study for exam" -> needs_image: false
- "Fix the broken shelf" -> needs_image: true, image_prompt: "Can I see the shelf?"

No other text, just the JSON object."""

    async def analyze_task_for_image(self, goal: str) -> Dict[str, Any]:
        """
        Analyze if a task would benefit from image context.
        Returns whether an image is needed and a prompt to ask the user.
        """
        if not self.settings.GEMINI_API_KEY or not GENAI_AVAILABLE:
            # Fallback: simple keyword-based detection
            return self._fallback_image_analysis(goal)
        
        prompt = f"""{self.IMAGE_ANALYSIS_PROMPT}

User's task: {goal}"""
        
        start_time = time.time()
        try:
            client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.settings.GEMINI_MODEL,
                    contents=prompt
                )
            )
            
            content = response.text
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the call
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_entry = [
                    "[LLM CALL] Gemini - Image Analysis",
                    f"Model: {self.settings.GEMINI_MODEL}",
                    f"Duration: {duration_ms:.2f}ms",
                    f"Goal: {goal}",
                    f"Response:\n{content}"
                ]
                log_to_file("\n".join(log_entry))
                print(f"📝 Logged LLM call: Image Analysis ({duration_ms:.2f}ms)")
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "needs_image": result.get("needs_image", False),
                    "image_prompt": result.get("image_prompt"),
                    "image_type": result.get("image_type")
                }
                
        except Exception as e:
            print(f"Image analysis error: {e}")
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_to_file(f"[LLM ERROR] Image Analysis: {str(e)}")
        
        return self._fallback_image_analysis(goal)
    
    def _fallback_image_analysis(self, goal: str) -> Dict[str, Any]:
        """Fallback keyword-based image analysis."""
        goal_lower = goal.lower()
        
        # Keywords that suggest visual context would help
        # Short, simple prompts - no emojis, max 10 words
        visual_keywords = {
            'clean': ('Can I see the space?', 'photo of space'),
            'tidy': ('Show me what needs tidying?', 'photo of area'),
            'organize': ('Can I see what to organize?', 'photo of items'),
            'room': ('Can I see your room?', 'photo of room'),
            'desk': ('Show me your desk?', 'photo of desk'),
            'closet': ('Can I see your closet?', 'photo of closet'),
            'garage': ('Show me your garage?', 'photo of garage'),
            'fix': ('Can I see what needs fixing?', 'photo of item'),
            'repair': ('Show me what needs repair?', 'photo of item'),
            'broken': ('Can I see what\'s broken?', 'photo of item'),
            'decorate': ('Can I see the space?', 'photo of space'),
            'rearrange': ('Show me the current setup?', 'photo of space'),
            'sort': ('Can I see what needs sorting?', 'photo of items'),
            'pack': ('Show me what you\'re packing?', 'photo of items'),
            'kitchen': ('Can I see your kitchen?', 'photo of kitchen'),
            'bathroom': ('Show me your bathroom?', 'photo of bathroom'),
            'garden': ('Can I see your garden?', 'photo of garden'),
            'yard': ('Show me your yard?', 'photo of yard'),
        }
        
        for keyword, (prompt_text, image_type) in visual_keywords.items():
            if keyword in goal_lower:
                return {
                    "needs_image": True,
                    "image_prompt": prompt_text,
                    "image_type": image_type
                }
        
        return {
            "needs_image": False,
            "image_prompt": None,
            "image_type": None
        }
    
    async def decompose_task_with_image(
        self, 
        goal: str, 
        image_base64: str, 
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Decompose a task with image context using Gemini's multimodal capabilities.
        """
        if not self.settings.GEMINI_API_KEY or not GENAI_AVAILABLE:
            # Fall back to text-only decomposition
            return await self.decompose_task(goal)
        
        # Mask PII in goal
        masked_goal, pii_map = self.pii_service.mask_text(goal)
        
        prompt = f"""{self.SYSTEM_PROMPT}

I'm sharing an image for context. Please analyze the image and break down this goal into specific, actionable micro-steps based on what you see.

Goal: {masked_goal}

Look at the image carefully and create steps that are specific to the actual situation shown."""
        
        start_time = time.time()
        try:
            client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
            
            # Prepare multimodal content with image
            contents = [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self.settings.GEMINI_MODEL,
                    contents=contents
                )
            )
            
            content = response.text
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the call (without full image data)
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_entry = [
                    "[LLM CALL] Gemini - Multimodal (with image)",
                    f"Model: {self.settings.GEMINI_MODEL}",
                    f"Duration: {duration_ms:.2f}ms",
                    f"Goal: {masked_goal}",
                    f"Image: {mime_type}, {len(image_base64)} bytes (base64)",
                    f"Response:\n{content}"
                ]
                log_to_file("\n".join(log_entry))
                print(f"📝 Logged LLM call: Multimodal ({duration_ms:.2f}ms)")
            
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
                
                # Calculate complexity
                complexity = self._calculate_complexity(goal, steps)
                
                # Unmask PII
                for step in steps:
                    step['action'] = self.pii_service.unmask_text(step['action'], pii_map)
                
                # Ensure bounds
                steps = steps[:10] if len(steps) > 10 else steps
                
                return {
                    "steps": steps,
                    "total_steps": len(steps),
                    "all_steps": steps,
                    "complexity_score": complexity
                }
                
        except Exception as e:
            print(f"Multimodal decomposition error: {e}")
            if LOGGER_AVAILABLE and self.settings.DEBUG:
                log_to_file(f"[LLM ERROR] Multimodal: {str(e)}")
        
        # Fallback to text-only
        return await self.decompose_task(goal)


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
