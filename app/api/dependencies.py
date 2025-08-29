from app.services.storage import video_storage
from app.services.ai_orchestrator import AIOrchestrator  # 
from app.services.video_processor import VideoProcessor

def get_video_storage():
    """Dependency for video storage service"""
    return video_storage

def get_script_generator():
    """Dependency for AI orchestrator service"""
    return AIOrchestrator()


def get_video_processor():
    """Dependency for video processor service"""
    return VideoProcessor()