import asyncio
import logging
import re
from typing import Optional
from app.core.config import settings
from app.core.exceptions import ScriptGenerationError
from app.services.aws_bedrock import BedrockService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Orchestrates AI model selection and script generation.
    Replaces the current ScriptGenerator with multi-model support.
    """
    
    def __init__(self):
        self.bedrock = BedrockService()
        self.openai = OpenAIService()

    async def generate_video_content(self, question: str, model: str, voice: str = "Joanna") -> dict:
        """Four-stage LLM pipeline per new specs: initial explanation -> refinement -> script -> validation."""
        try:
            logger.info(f"🎯 Pipeline start ({model}) for question")

            # Stage 1: Initial natural language explanation
            stage1_prompt = self._prompt_initial_explanation(question)
            initial_explanation = await self._llm(model, stage1_prompt)

            # Stage 2: Refinement of the explanation
            stage2_prompt = self._prompt_refine_explanation(initial_explanation)
            refined_explanation = await self._llm("gpt-5", stage2_prompt)

            # Stage 3: Generate Manim script from refined explanation
            stage3_prompt = self._prompt_generate_script(refined_explanation)
            manim_script = await self._llm("claude-4-sonnet", stage3_prompt)

            # Stage 4: Validate/fix Manim scriptß
            stage4_prompt = self._prompt_validate_script(manim_script)
            validated_script = await self._llm("claude-4-sonnet", stage4_prompt)

            # Stage 5: Visual validation for overlaying shapes, numbers, and pictures
            stage5_prompt = self._prompt_validate_visual_elements(validated_script)
            visual_validated_script = await self._llm("claude-4-sonnet", stage5_prompt)

            # Optional voiceover can be applied later as needed
            logger.info(f"✅ Pipeline completed: explanation ({len(refined_explanation)} chars), script ({len(visual_validated_script)} chars)")

            # Add voiceover and return only final script
            final_script = await self._add_voiceover_functionality(visual_validated_script, question, model, voice)
            return final_script
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise ScriptGenerationError(f"Pipeline failed: {str(e)}")

    async def _llm(self, model: str, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        """DRY unified inference: route to OpenAI or Bedrock with prepared prompts."""
        if model == 'gpt-5':
            return await self.openai.model_call(user_prompt=user_prompt, system_prompt=system_prompt, model="gpt-5")
        elif model in settings.BEDROCK_MODELS:
            # Bedrock ignores system prompt in current impl; include in user prompt if provided
            merged_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
            return await self.bedrock.model_call(merged_prompt, model)
        else:
            raise ValueError(f"Unsupported model: {model}")

    def _prompt_initial_explanation(self, question: str) -> str:
        # Use concise educator system converted to user prompt for cross-provider parity
        return  self.bedrock._natural_language_explanation(question)

    def _prompt_refine_explanation(self, explanation: str) -> str:
        return  self.bedrock._verify_natural_language_explanation(explanation)

    def _prompt_generate_script(self, refined_explanation: str) -> str:
        return  self.bedrock._build_manim_prompt(refined_explanation)

    def _prompt_validate_script(self, script_content: str) -> str:
        return f"""
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

    def _prompt_validate_visual_elements(self, script_content: str) -> str:
        return f"""
Review this Manim script specifically for VISUAL COMPOSITION and ELEMENT OVERLAPPING issues. Fix any problems with shapes, numbers, pictures, and text positioning. Return ONLY the corrected Python code.

CRITICAL VISUAL VALIDATION CHECKS:

1. **OVERLAPPING ELEMENTS**:
   - Check if shapes, text, or objects overlap unintentionally
   - Ensure numbers and labels are clearly visible and not hidden behind shapes
   - Fix any z-index issues with layering of visual elements
   - Use proper spacing between elements

2. **POSITIONING AND ALIGNMENT**:
   - Verify all elements are positioned within the visible frame
   - Check that text labels are properly aligned with their corresponding shapes
   - Ensure mathematical expressions and numbers are clearly readable
   - Fix any elements that appear outside the screen boundaries

3. **VISUAL HIERARCHY**:
   - Ensure important elements (numbers, labels, key shapes) are prominently displayed
   - Check that background elements don't overshadow foreground content
   - Verify proper contrast between text and background colors
   - Fix any visual clutter or confusing arrangements

4. **SHAPE AND OBJECT CLARITY**:
   - Ensure geometric shapes are clearly defined and visible
   - Check that lines, arrows, and connectors are properly positioned
   - Verify that mathematical diagrams maintain their logical structure
   - Fix any distorted or improperly scaled elements

5. **TEXT AND NUMBERING**:
   - Ensure all text is readable and properly sized
   - Check that mathematical expressions render correctly
   - Verify that step numbers or labels are clearly visible
   - Fix any text that overlaps with shapes or other elements

6. **ANIMATION SEQUENCE**:
   - Check that visual elements appear in logical order
   - Ensure animations don't cause temporary overlapping issues
   - Verify that elements remain visible throughout their intended duration
   - Fix any timing issues that cause visual confusion

SCRIPT TO VALIDATE:
```python
{script_content}
```

Return ONLY the visually optimized Python code with improved positioning, spacing, and element arrangement."""

    async def _add_voiceover_functionality(self, script_content: str, original_prompt: str, model: str, voice: str = "Joanna") -> str:
        """Add voiceover functionality to the script using individual services"""
        try:
            logger.info(f"🎙️ Adding voiceover functionality with {model}...")
            
            # Use the new voiceover methods from individual services
            if model == 'gpt-5':
                voiceover_script = await self.openai.add_voiceover_functionality(script_content, original_prompt, voice)
            else:
                voiceover_script = await self.bedrock.add_voiceover_functionality(script_content, original_prompt, model, voice)
            
            cleaned_voiceover = self._clean_script(voiceover_script)
            
            # Ensure Polly imports are correct (will be copied to temp dir)
            cleaned_voiceover = self._ensure_polly_imports(cleaned_voiceover)
            
            # Validate that voiceover imports were added (SAME AS ORIGINAL)
            if 'VoiceoverScene' not in cleaned_voiceover:
                logger.warning("Voiceover integration may have failed, VoiceoverScene not found")
                # Add imports if missing (SAME AS ORIGINAL)
                if 'from manim_voiceover' not in cleaned_voiceover:
                    cleaned_voiceover = self._add_voiceover_imports(cleaned_voiceover)
                # Convert Scene to VoiceoverScene (SAME AS ORIGINAL)
                cleaned_voiceover = re.sub(r'class\s+(\w+)\s*\(\s*Scene\s*\):', r'class \1(VoiceoverScene):', cleaned_voiceover)
            
            logger.info(f"✅ Voiceover integration completed")
            return cleaned_voiceover
            
        except Exception as e:
            logger.warning(f"Voiceover integration failed: {e}, using basic structure")
            return self._add_basic_voiceover_structure(script_content, voice)

    def _clean_script(self, script_content: str) -> str:
        """Clean and validate the generated script (same as current implementation)"""
        import re
        
        logger.debug(f"Cleaning script content...")
        
        # Remove markdown code blocks
        script_content = re.sub(r'```python\s*\n', '', script_content)
        script_content = re.sub(r'```\s*$', '', script_content, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        script_content = script_content.strip()
        
        # Fix common issues (same as current implementation)
        script_content = self._fix_common_issues(script_content)
        
        return script_content

    def _fix_common_issues(self, script_content: str) -> str:
        """Fix common issues that cause Manim errors (same as current implementation)"""
        import re
        
        # Replace problematic VGroup(*self.mobjects) pattern
        script_content = re.sub(
            r'VGroup\(\*self\.mobjects\)',
            'Group(*[mob for mob in self.mobjects if hasattr(mob, "animate")])',
            script_content
        )
        
        # Fix vector normalization issues
        script_content = re.sub(
            r'([a-zA-Z_][a-zA-Z0-9_]*(?:\s*[-+]\s*[a-zA-Z_][a-zA-Z0-9_]*)?)\.normalize\(\)',
            r'(\1 / np.linalg.norm(\1))',
            script_content
        )
        
        # Ensure numpy is imported if vector operations are used
        if 'np.linalg.norm' in script_content and 'import numpy as np' not in script_content:
            script_content = 'import numpy as np\n' + script_content
        
        return script_content

    def _ensure_polly_imports(self, script_content: str) -> str:
        """Ensure correct AWS Polly imports are present"""
        import re
        
        # Ensure we have the correct import if VoiceoverScene is present
        if 'VoiceoverScene' in script_content and 'create_polly_service' not in script_content:
            if 'from manim import *' in script_content:
                script_content = script_content.replace(
                    'from manim import *',
                    'from manim import *\nfrom app.services.aws_polly import create_polly_service'
                )
            else:
                script_content = 'from app.services.aws_polly import create_polly_service\n' + script_content
        
        return script_content

    def _add_voiceover_imports(self, script_content: str) -> str:
        """Add necessary voiceover imports to the script (SAME AS ORIGINAL)"""
        import re
        
        # Find the existing imports section
        if 'from manim import *' in script_content:
            script_content = script_content.replace(
                'from manim import *',
                'from manim import *\nfrom manim_voiceover import VoiceoverScene\nfrom app.services.aws_polly import create_polly_service'
            )
        else:
            # Add imports at the beginning
            script_content = 'from manim import *\nfrom manim_voiceover import VoiceoverScene\nfrom app.services.aws_polly import create_polly_service\n\n' + script_content
        
        return script_content

    def _add_basic_voiceover_structure(self, script_content: str, voice: str = "Joanna") -> str:
        """Add basic voiceover structure if AI integration fails"""
        import re
        
        # Add imports
        if 'from manim_voiceover' not in script_content:
            script_content = 'from manim_voiceover import VoiceoverScene\nfrom app.services.aws_polly import create_polly_service\n' + script_content
        
        # Convert Scene to VoiceoverScene
        script_content = re.sub(r'class\s+(\w+)\s*\(\s*Scene\s*\):', r'class \1(VoiceoverScene):', script_content)
        
        # Add speech service initialization with dynamic voice
        speech_service_init = f'''        # Initialize speech service
        self.set_speech_service(
            create_polly_service(
                voice="{voice}",
                style="friendly"
            )
        )

'''
        
        # Find construct method and add speech service
        script_content = re.sub(
            r'(def construct\(self\):\s*\n)',
            r'\1' + speech_service_init,
            script_content
        )
        
        return script_content