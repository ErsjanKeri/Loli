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

    async def generate_script(self, prompt: str, model: str) -> str:
        """
        Generate Manim script using specified model.
        
        Args:
            prompt: Educational content prompt
            model: Model name (from BEDROCK_MODELS or 'gpt-5')
            
        Returns:
            Generated Manim script content
        """
        try:
            logger.info(f"🎯 AI Orchestrator: Generating script with {model}")
            
            # Route to appropriate service based on model
            if model == 'gpt-5':
                # OpenAI ChatGPT-5
                script_content = await self.openai.generate_script(prompt)
            elif model in settings.BEDROCK_MODELS:
                # AWS Bedrock models
                script_content = await self.bedrock.generate_script(prompt, model)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            # Clean and validate the script
            cleaned_script = self._clean_script(script_content)
            
            # Validate the script 
            validated_script = await self._validate_script(cleaned_script, model)
            
            # Add voiceover 
            final_script = await self._add_voiceover_functionality(validated_script, prompt, model)
            
            logger.info(f"✅ AI Orchestrator: Final script ready ({len(final_script)} chars)")
            return final_script
            
        except Exception as e:
            logger.error(f"❌ AI Orchestrator failed: {e}")
            raise ScriptGenerationError(f"Script generation failed: {str(e)}")

    async def _validate_script(self, script_content: str, model: str) -> str:
        """Validate and fix the script using the same model that generated it"""
        try:
            logger.info(f"🔍 Validating script with {model}...")
            
            # Use the new validation methods from individual services
            if model == 'gpt-5':
                validated_script = await self.openai.validate_script(script_content)
            else:
                validated_script = await self.bedrock.validate_script(script_content, model)
            
            cleaned_validated = self._clean_script(validated_script)
            logger.info(f"✅ Script validation completed")
            return cleaned_validated
            
        except Exception as e:
            logger.warning(f"Script validation failed: {e}, using original script")
            return script_content

    async def _add_voiceover_functionality(self, script_content: str, original_prompt: str, model: str) -> str:
        """Add voiceover functionality to the script using individual services"""
        try:
            logger.info(f"🎙️ Adding voiceover functionality with {model}...")
            
            # Use the new voiceover methods from individual services
            if model == 'gpt-5':
                voiceover_script = await self.openai.add_voiceover_functionality(script_content, original_prompt)
            else:
                voiceover_script = await self.bedrock.add_voiceover_functionality(script_content, original_prompt, model)
            
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
            return self._add_basic_voiceover_structure(script_content)

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

    def _add_basic_voiceover_structure(self, script_content: str) -> str:
        """Add basic voiceover structure if AI integration fails"""
        import re
        
        # Add imports
        if 'from manim_voiceover' not in script_content:
            script_content = 'from manim_voiceover import VoiceoverScene\nfrom app.services.aws_polly import create_polly_service\n' + script_content
        
        # Convert Scene to VoiceoverScene
        script_content = re.sub(r'class\s+(\w+)\s*\(\s*Scene\s*\):', r'class \1(VoiceoverScene):', script_content)
        
        # Add speech service initialization
        speech_service_init = '''        # Initialize speech service
        self.set_speech_service(
            create_polly_service(
                voice="Joanna",
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
