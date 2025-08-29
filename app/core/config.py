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

    # Available Models (Updated for eu-west-3 region)
    BEDROCK_MODELS: list = [
        "claude-3-5-sonnet",
        "claude-3-5-sonnet-v2", 
        "claude-3-7-sonnet",
        "claude-4-sonnet",
        "claude-3-sonnet",
        "claude-3-haiku"
    ]
    
    # AWS Polly Settings (NEW)
    DEFAULT_VOICE: str = "Joanna"
    AVAILABLE_VOICES: list = ["Joanna", "Matthew", "Ruth", "Stephen"]

    # Storage Settings - Fixed for Windows compatibility
    VIDEOS_DIR: str = "generated_videos"
    TEMP_DIR: str = get_temp_dir()

    # Video Settings
    MAX_VIDEO_DURATION: int = 30  # 0.5 minutes - content duration limit
    MANIM_PROCESSING_TIMEOUT: int = 300  # 5 minutes for regular videos
    CLEANUP_INTERVAL: int = 3600  # 1 hour

    # Performance Settings
    MAX_CONCURRENT_VIDEOS: int = 2  # Reduced further for voiceover stability
    VIDEO_RETENTION_DAYS: int = 7

    class Config:
        env_file = "app/.env"


settings = Settings()