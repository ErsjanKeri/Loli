"""
AWS Polly Text-to-Speech Service for Manim Voiceover Integration

This service provides a drop-in replacement for Azure TTS, maintaining
the same interface while using AWS Polly for voice generation.
"""

import asyncio
import hashlib
import logging
import os
import tempfile
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from manim_voiceover.services.base import SpeechService

from app.core.config import settings

logger = logging.getLogger(__name__)


class PollyService(SpeechService):
    """
    AWS Polly service that extends manim-voiceover SpeechService
    for seamless integration with existing Manim voiceover functionality.
    """
    
    def __init__(self, voice: str = "Joanna", style: str = "friendly", **kwargs):
        """
        Initialize AWS Polly service
        
        Args:
            voice: AWS Polly voice name (e.g., "Joanna", "Matthew", "Ruth")
            style: Style parameter (maintained for compatibility, not used by Polly)
        """
        super().__init__(**kwargs)
        self.voice = voice
        self.style = style
        
        # Initialize AWS Polly client
        self.client = boto3.client(
            'polly',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"🎤 AWS Polly service initialized with voice: {voice}")
    
    def generate_from_text(self, text: str, cache_dir: Optional[str] = None, **kwargs) -> str:
        """
        Generate speech from text using AWS Polly (manim-voiceover interface)
        
        Args:
            text: Text to convert to speech
            cache_dir: Directory to cache audio files
            **kwargs: Additional arguments
            
        Returns:
            Path to generated audio file
        """
        try:
            # Create cache directory if needed
            if cache_dir is None:
                cache_dir = self.cache_dir
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create unique filename based on text and voice
            text_hash = hashlib.md5(f"{text}_{self.voice}".encode()).hexdigest()
            audio_file = os.path.join(cache_dir, f"polly_{text_hash}.mp3")
            
            # Generate if not cached
            if not os.path.exists(audio_file):
                logger.debug(f"Generating speech for: {text[:50]}...")
                
                # Try SSML first, fallback to plain text
                try:
                    ssml_text = self._wrap_with_ssml(text)
                    response = self.client.synthesize_speech(
                        Text=ssml_text,
                        TextType='ssml',
                        OutputFormat='mp3',
                        VoiceId=self.voice,
                        Engine='standard'
                    )
                except ClientError as ssml_error:
                    logger.warning(f"SSML failed, trying plain text: {ssml_error}")
                    # Fallback to plain text if SSML fails
                    response = self.client.synthesize_speech(
                        Text=text,
                        TextType='text',
                        OutputFormat='mp3',
                        VoiceId=self.voice,
                        Engine='standard'
                    )
                
                # Save the audio stream to file
                with open(audio_file, 'wb') as file:
                    file.write(response['AudioStream'].read())
                
                logger.debug(f"✅ Speech generated successfully: {audio_file}")
            else:
                logger.debug(f"Using cached speech: {audio_file}")
            
            # Return dictionary format expected by manim-voiceover
            return {
                "original_audio": audio_file,
                "final_audio": os.path.basename(audio_file)
            }
            
        except ClientError as e:
            logger.error(f"❌ AWS Polly error: {e}")
            raise Exception(f"Polly synthesis failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Speech generation failed: {e}")
            raise Exception(f"Speech generation failed: {str(e)}")
    
    def _wrap_with_ssml(self, text: str) -> str:
        """
        Wrap text with basic SSML for speech synthesis
        
        Args:
            text: Plain text to wrap
            
        Returns:
            SSML-formatted text
        """
        # Simple SSML wrapper with basic pauses
        ssml_text = text.replace('. ', '.<break time="0.5s"/> ')
        
        # Basic SSML speak tags
        return f'<speak>{ssml_text}</speak>'


def create_polly_service(voice: str = None, style: str = "friendly") -> PollyService:
    """
    Factory function to create AWS Polly service with configured voice
    
    Args:
        voice: Voice to use (defaults to configured voice)
        style: Style parameter (for compatibility)
        
    Returns:
        Configured AWS Polly service
    """
    voice = voice or settings.DEFAULT_VOICE
    return PollyService(voice=voice, style=style)