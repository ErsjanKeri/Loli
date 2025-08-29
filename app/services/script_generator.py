import logging

logger = logging.getLogger(__name__)

# Deprecated: This module has been replaced by AIOrchestrator.generate_video_content
# Kept as a stub for backward compatibility to avoid import errors.

class ScriptGenerator:
    def __init__(self):
        logger.warning("ScriptGenerator is deprecated. Use AIOrchestrator.generate_video_content instead.")

    async def generate_script(self, prompt: str, model: str) -> str:
        raise NotImplementedError("Use AIOrchestrator.generate_video_content for the new LLM pipeline.")