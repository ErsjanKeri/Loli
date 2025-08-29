import openai
import asyncio
import logging
from typing import Optional
from app.core.config import settings
from app.core.exceptions import ScriptGenerationError

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    async def model_call(self, user_prompt: str, system_prompt: Optional[str] = None, model: str = "gpt-5") -> str:
        """Generic OpenAI chat completion call returning content only."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI model_call failed: {e}")
            raise ScriptGenerationError(f"OpenAI call failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        return """You are an expert Manim script generator specializing in educational content.
        Generate clean, executable Python code that creates engaging mathematical animations.
        Focus on clarity, visual appeal, and educational value.
        Follow all the requirements provided in the user prompt exactly."""

    def _build_manim_prompt(self, prompt: str) -> str:
        """Build enhanced prompt for Manim script generation (PROVEN ORIGINAL VERSION - SAFER)"""
        return f"""
        Create a complete Manim script that explains: {prompt}

        CRITICAL REQUIREMENTS:
        - Use the latest Manim syntax (from manim import *)
        - Import numpy as np if you need vector operations
        - Create a class that inherits from Scene (voiceover will be added later)
        - NEVER use VGroup(*self.mobjects) - this causes errors
        - Instead use Group() or create specific groups of objects
        - Use VMobject types for grouping (Text, Circle, Rectangle, etc.)
        - Avoid mixing Mobject and VMobject types
        - Keep the animation between 10-30 seconds
        - Make sure all imports are correct
        - End with self.wait(2) for a clean finish
        - Use Text() instead of MathTex for better compatibility
        - Use simple, reliable Manim objects

        VECTOR OPERATIONS:
        - NEVER use .normalize() on numpy arrays - this method doesn't exist
        - Use np.linalg.norm() for vector normalization: vector / np.linalg.norm(vector)
        - Example: normalized = (point_a - point_b) / np.linalg.norm(point_a - point_b)
        - Always complete your lines of code - don't leave hanging expressions

        APPROVED IMPORTS ONLY:
        - from manim import *
        - import numpy as np
        - import math, random, itertools
        - import sympy as sp (if needed)
        - import networkx as nx (if needed)

        SAFE OBJECT TYPES TO USE:
        - Text() for all text
        - Circle(), Rectangle(), Square() for shapes
        - Line(), Arrow() for connections
        - Group() for grouping objects (NOT VGroup(*self.mobjects))
        - NumberPlane(), Axes() for coordinate systems

        CRITICAL POSITIONING RULES:
        - NEVER use .surround() method - it doesn't exist in current Manim
        - NEVER use buffer parameter with Circle() - it doesn't exist
        - Use .move_to(object.get_center()) to position objects around others
        - Use .next_to(object, direction) for relative positioning
        - Use .shift(direction * distance) for manual positioning
        - Example: circle.move_to(text.get_center()) NOT circle.surround(text, buffer=0.3)

        ANIMATION RULES:
        - Use Create() ONLY on individual objects (Circle, Rectangle, Line, Text, etc.)
        - NEVER use Create(group), Write(group), or FadeIn(group) - this causes "NotImplementedError"
        - For groups, animate each object separately: self.play(*[Create(obj) for obj in group])
        - Alternative for groups: self.play(Create(obj1), Create(obj2), Create(obj3))
        - For VGroups/Groups: Use AnimationGroup or animate individual members
        - Example: self.play(*[Write(obj) for obj in my_group]) instead of Write(my_group)

        SAFE COLORS TO USE (ONLY THESE):
        - RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK
        - WHITE, BLACK, GRAY, GREY, LIGHT_GRAY, DARK_GRAY
        - TEAL, MAROON, GOLD
        - For custom colors use: "#FF5733" or "#3498DB" (hex format)

        NOTE: This script will later be enhanced with voiceover functionality, so focus on clear visual storytelling.

        Return ONLY the Python code without explanations or markdown formatting.
        """

    async def validate_script(self, script_content: str) -> str:
        """Second GPT-5 call to validate and fix the script (COPIED from script_generator.py)"""
        validation_prompt = f"""
Review this Manim script and fix any issues to make it executable. Return ONLY the corrected Python code.

CRITICAL FIXES NEEDED:
- Ensure all imports are correct (from manim import *)
- Fix any syntax errors
- Make sure the class inherits from Scene properly
- Fix any undefined variables or functions
- Ensure all colors used are valid Manim colors
- CRITICAL: Fix animation on groups - NEVER use Create(group), Write(group), or FadeIn(group)
- For groups use: self.play(*[Create(obj) for obj in group]) or animate each member individually
- Make sure all objects are properly defined before use
- Ensure proper indentation
- IMPORTANT: Fix vector normalization - use np.linalg.norm() instead of .normalize()
- Import numpy as np if needed for vector operations
- Complete any incomplete lines of code

SCRIPT TO FIX:
```python
{script_content}
```

Return ONLY the fixed Python code, no explanations or markdown.
"""
        try:
            fixed_script = await self.model_call(
                user_prompt=validation_prompt,
                system_prompt="Fix Manim scripts to be executable. Return only clean Python code.",
                model="gpt-5",
            )
            logger.info(f"✅ Script validation completed")
            return fixed_script
        except Exception as e:
            logger.warning(f"Script validation failed: {e}, using original script")
            return script_content

    async def add_voiceover_functionality(self, script_content: str, original_prompt: str, voice: str = "Joanna") -> str:
        """Third GPT-5 call to add voiceover functionality (COPIED from script_generator.py + AWS POLLY)"""
        voiceover_prompt = f"""
Transform this Manim script to use voiceover functionality. The original educational topic was: "{original_prompt}"

CRITICAL REQUIREMENTS FOR VOICEOVER INTEGRATION:
1. Change the class to inherit from VoiceoverScene instead of Scene
2. Import: from manim_voiceover import VoiceoverScene
3. Import: from app.services.aws_polly import create_polly_service
4. Add speech service initialization in construct method:
   self.set_speech_service(create_polly_service(voice="{voice}", style="friendly"))
5. Wrap animation sequences with voiceover context managers
6. Use this pattern: with self.voiceover(text="Narration text here") as tracker:
7. Sync animations with voiceover duration using tracker.duration
8. Write natural, educational narration that explains what's happening
9. Keep the same visual content and animations, just add voiceover

VOICEOVER PATTERNS TO USE:
- with self.voiceover(text="Introduction text") as tracker:
    self.play(Write(title), run_time=tracker.duration)

- with self.voiceover(text="Explanation text") as tracker:
    self.play(Create(shape), run_time=tracker.duration - 0.5)
    self.wait(0.5)

NARRATION GUIDELINES:
- Write clear, educational narration
- Explain concepts as they appear visually
- Use natural, conversational language
- Match narration length to animation duration
- Include brief pauses with self.wait() when needed

EXISTING SCRIPT TO TRANSFORM:
```python
{script_content}
```

Return ONLY the complete transformed Python code with voiceover integration, no explanations or markdown.
"""
        try:
            voiceover_script = await self.model_call(
                user_prompt=voiceover_prompt,
                system_prompt="Transform Manim scripts to use AWS Polly voiceover. Use 'from app.services.aws_polly import create_polly_service' for TTS integration.",
                model="gpt-5",
            )
            logger.info(f"✅ Voiceover integration completed")
            return voiceover_script
        except Exception as e:
            logger.warning(f"Voiceover integration failed: {e}, using original script")
            return script_content
