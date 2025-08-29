from pydantic_settings import BaseSettings
import os
import platform
from dotenv import load_dotenv

load_dotenv("app/.env")

def get_temp_dir() -> str:
    """Platform-specific temp directory"""
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "manim_videos")
    else:
        return "/tmp/manim_videos"


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "DEBUG"

    # AWS Configuration (NEW)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # S3 Configuration (NEW)
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "loli-bucket")
    S3_REGION: str = os.getenv("S3_REGION", "eu-west-3")  # Same as AWS_REGION for consistency

    # OpenAI Configuration (NEW)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Available Models (2025 Updated Lineup)
    BEDROCK_MODELS: list = [
        "titan-text-g1-express",
        "nova-pro", 
        "claude-4-sonnet",
        "llama-3-2-3b-instruct",
        "mixtral-8x7b-instruct"
    ]
    
    # OpenAI Models (Special handling)
    OPENAI_MODELS: list = [
        "gpt-5"
    ]
    
    # All available models for frontend
    ALL_MODELS: list = BEDROCK_MODELS + OPENAI_MODELS
    
    # AWS Polly Settings - 2025 Enhanced Neural Voices
    DEFAULT_VOICE: str = "Joanna"
    AVAILABLE_VOICES: list = [
        # US English Neural Voices
        "Joanna",      # Female, warm and friendly
        "Matthew",     # Male, professional and clear
        "Kimberly",    # Female, young and energetic
        "Justin",      # Male, confident and engaging
        "Joey",        # Male, casual and approachable
        "Ivy",         # Female, calm and sophisticated
        "Kendra",      # Female, authoritative and clear
        "Kevin",       # Male, dynamic and expressive
        "Salli",       # Female, gentle and reassuring
        "Ruth",        # Female, mature and wise
        "Stephen",     # Male, distinguished and articulate
        # British English Neural Voices
        "Amy",         # Female, British accent
        "Emma",        # Female, British accent, youthful
        "Brian",       # Male, British accent
        "Arthur",      # Male, British accent, mature
        # Additional International Voices
        "Olivia",      # Female, Australian accent
        "Aria",        # Female, New Zealand accent
    ]

    # Storage Settings - Fixed for Windows compatibility
    VIDEOS_DIR: str = "generated_videos"
    TEMP_DIR: str = get_temp_dir()

    # Video Settings
    MAX_VIDEO_DURATION: int = 30  # Content duration limit in seconds
    MANIM_PROCESSING_TIMEOUT: int = 300  # Processing timeout in seconds
    CLEANUP_INTERVAL: int = 3600  # Cleanup interval in seconds

    # Performance Settings
    MAX_CONCURRENT_VIDEOS: int = 2  # Reduced further for voiceover stability
    VIDEO_RETENTION_DAYS: int = 7

    class Config:
        env_file = "app/.env"


settings = Settings()