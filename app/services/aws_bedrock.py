import boto3
import json
import asyncio
import logging
from typing import Dict, Optional
from app.core.config import settings
from app.core.exceptions import ScriptGenerationError

logger = logging.getLogger(__name__)


class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Reverted to original in-repo defaults; can be overridden by env variables below
        self.model_ids = {
            'claude-4-sonnet': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
            'claude-opus-4': 'us.anthropic.claude-opus-4-20250514-v1:0',
            'claude-opus-4-1': 'us.anthropic.claude-opus-4-1-20250805-v1:0',
            'claude-3-7-sonnet': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            'claude-3-5-sonnet-v2': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            'claude-3-5-haiku': 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
            'claude-3-sonnet': 'us.anthropic.claude-3-sonnet-20240229-v1:0',
        }

    async def model_call(self, prompt: str, model: str) -> str:
        """Generic Bedrock call: accepts a prepared user prompt and returns text content."""
        try:
            model_id = self.model_ids.get(model)
            if not model_id:
                raise ValueError(f"Unsupported model: {model}")
            logger.info(f"🤖 Calling AWS Bedrock ({model})...")
            body = self.format_model_request(model, prompt)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._call_bedrock_sync, 
                model_id,
                body
            )
            text = self._extract_content(response, model)
            logger.info(f"✅ Bedrock {model} response ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"❌ Bedrock call failed: {e}")
            raise ScriptGenerationError(f"Bedrock generation failed: {str(e)}")
    
    def format_model_request(self, model: str, model_request: str) -> str:
        """Process the output from the Bedrock model"""
        # Format request based on model family
        if model.startswith('claude'):
            body = self._format_claude_request(model_request)
        elif model.startswith('llama'):
            body = self._format_llama_request(model_request)
        elif model.startswith('amazon-titan'):
            body = self._format_titan_request(model_request)
        elif model.startswith('cohere'):
            body = self._format_cohere_request(model_request)
        elif model.startswith('ai21'):
            body = self._format_ai21_request(model_request)
        elif model.startswith('mistral'):
            body = self._format_mistral_request(model_request)
        else:
            raise ValueError(f"Unknown model family for: {model}")
        return body
    
    def _call_bedrock_sync(self, model_id: str, body: Dict) -> Dict:
        """Synchronous call to Bedrock (runs in executor)"""
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        return json.loads(response['body'].read())

    def _format_claude_request(self, prompt: str) -> Dict:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

    def _format_llama_request(self, prompt: str) -> Dict:
        return {
            "prompt": prompt,
            "max_gen_len": 4000,
            "temperature": 0.1,
            "top_p": 0.9
        }

    def _format_titan_request(self, prompt: str) -> Dict:
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 4000,
                "temperature": 0.1,
                "topP": 0.9
            }
        }

    def _format_cohere_request(self, prompt: str) -> Dict:
        return {
            "message": prompt,
            "max_tokens": 4000,
            "temperature": 0.1,
            "p": 0.9
        }

    def _format_ai21_request(self, prompt: str) -> Dict:
        return {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9
        }

    def _format_mistral_request(self, prompt: str) -> Dict:
        return {
            "prompt": prompt,
            "max_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9
        }

    def _extract_content(self, response: Dict, model: str) -> str:
        """Extract text content from model response"""
        if model.startswith('claude'):
            return response['content'][0]['text']
        elif model.startswith('llama'):
            return response['generation']
        elif model.startswith('amazon-titan'):
            return response['results'][0]['outputText']
        elif model.startswith('cohere'):
            return response['text']
        elif model.startswith('ai21'):
            return response['choices'][0]['message']['content']
        elif model.startswith('mistral'):
            return response['outputs'][0]['text']
        else:
            raise ValueError(f"Unknown response format for model: {model}")


    def _natural_language_explanation(self, prompt: str) -> str:
        """Build a natural language explanation for the prompt"""
        return f"""
        You are an expert educator specializing in creating clear, step-by-step explanations of technical concepts. Your task is to explain the following technical term or concept: {prompt}

        EXPLANATION REQUIREMENTS:
        1. STRUCTURE: Organize your explanation in a logical, progressive sequence
        2. CLARITY: Use simple, accessible language that avoids unnecessary jargon
        3. EXAMPLES: Provide concrete, real-world examples that illustrate each step
        4. VISUAL THINKING: Include analogies or comparisons that help visualize the concept
        5. BUILDING BLOCKS: Start with fundamental concepts and gradually build complexity

        FORMAT GUIDELINES:
        - Begin with a brief, clear definition
        - Break down the concept into 3-5 logical steps
        - For each step, provide a simple example or analogy
        - Use everyday objects or situations when possible
        - End with a practical application or summary

        EXAMPLE STRUCTURE:
        1. "What is [concept]?" - Simple definition
        2. "Step 1: [First fundamental aspect]" - With concrete example
        3. "Step 2: [Second aspect]" - With relatable analogy
        4. "Step 3: [How it works]" - With practical demonstration
        5. "Real-world application or analogy" - Where you might encounter this or how it could be imagined or drawn 

        TONE: Friendly, patient, and encouraging. Assume the reader is intelligent but new to this concept.

        Return ONLY the natural language explanation following this structure, no explanations or markdown formatting.
        """
    
    def _verify_natural_language_explanation(self, prompt: str) -> str:
        """Verify the natural language explanation is correct"""
        return f"""
        You are an expert educational content reviewer. Analyze this explanation for weak points and improve it: {prompt}

        FIND AND FIX:
        - Logical errors, contradictions, or gaps
        - Factual inaccuracies or unclear language
        - Poor examples or weak analogies
        - Missing information or incomplete explanations
        - Structural problems or poor organization
        - Inappropriate complexity level
        - Unclear or confusing statements

        IMPROVE TO:
        - Clear, logical progression from simple to complex
        - Accurate technical information with helpful examples
        - Accessible language with concrete analogies
        - Complete coverage with visual descriptions
        - Engaging tone suitable for video scripts

        CRITICAL REQUIREMENT: You MUST return ONLY a REFINED AND IMPROVED VERSION of the original explanation that addresses all identified issues. This refined version should be:

        - Logically structured and coherent
        - Technically accurate and up-to-date
        - Clear and accessible to the target audience
        - Rich with relevant examples and analogies
        - Visually descriptive for video script generation
        - Engaging and well-paced
        - Complete and comprehensive
        - Ready for immediate use in educational content

        RETURN ONLY THE REFINED EXPLANATION TEXT - no analysis, no markdown, no additional commentary.
        """
    

    # TODO: Add a prompt builder for the Bedrock models
    def _build_manim_prompt(self, prompt: str) -> str:
        """Build enhanced prompt for Manim script generation (PROVEN ORIGINAL VERSION - SAFER)"""
        return f"""
        Create a complete Manim script that visually shows the following concept that is explained in the natural language explanation: {prompt}

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

    async def validate_script(self, script_content: str, model: str) -> str:
        """Validate and fix the script using the same Bedrock model (COPIED from script_generator.py)"""
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
            validated_script = await self.model_call(validation_prompt, model)
            logger.info(f"✅ Bedrock script validation completed")
            return validated_script
            
        except Exception as e:
            logger.warning(f"Bedrock script validation failed: {e}, using original script")
            return script_content

    async def add_voiceover_functionality(self, script_content: str, original_prompt: str, model: str) -> str:
        """Add voiceover functionality using Bedrock model (COPIED from script_generator.py + AWS POLLY)"""
        voiceover_prompt = f"""
Transform this Manim script to use voiceover functionality. The original educational topic was: "{original_prompt}"

CRITICAL REQUIREMENTS FOR VOICEOVER INTEGRATION:
1. Change the class to inherit from VoiceoverScene instead of Scene
2. Import: from manim_voiceover import VoiceoverScene
3. Import: from app.services.aws_polly import create_polly_service
4. Add speech service initialization in construct method:
   self.set_speech_service(create_polly_service(voice="Joanna", style="friendly"))
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
            voiceover_script = await self.model_call(voiceover_prompt, model)
            logger.info(f"✅ Bedrock voiceover integration completed")
            return voiceover_script
            
        except Exception as e:
            logger.warning(f"Bedrock voiceover integration failed: {e}, using original script")
            return script_content


"""
  APPROVED IMPORTS ONLY:
        - from manim import *
        - import numpy as np
        - import math, random, itertools
        - import sympy as sp (if needed)
        - import networkx as nx (if needed)
"""