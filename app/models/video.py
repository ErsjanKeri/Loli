from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class VideoStatus(str, Enum):
    QUEUED = "queued"
    GENERATING_SCRIPT = "generating_script"
    RENDERING_VIDEO = "rendering_video"
    UPLOADING_TO_S3 = "uploading_to_s3"
    COMPLETED = "completed"
    COMPLETED_WITHOUT_S3 = "completed_without_s3"
    FAILED = "failed"

class VideoRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=10000, description="Description of the educational video to generate")
    # NEW: Model selection
    model: Optional[str] = Field(default="claude-4-sonnet", description="AI model to use for script generation")
    # NEW: Voice selection  
    voice: Optional[str] = Field(default="Joanna", description="Voice to use for narration")

class VideoResponse(BaseModel):
    video_id: str
    status: VideoStatus
    message: str
    video_url: Optional[str] = None  # Legacy support
    s3_url: Optional[str] = None     # New S3 public URL
    created_at: datetime
    progress: Optional[int] = Field(default=0, ge=0, le=100, description="Generation progress percentage")

class VideoInfo(BaseModel):
    video_id: str
    status: VideoStatus
    message: str
    video_path: Optional[str] = None  # Local file path
    s3_url: Optional[str] = None      # S3 public URL
    created_at: datetime
    script_content: Optional[str] = None
    error_details: Optional[str] = None
    progress: int = 0
    prompt: Optional[str] = None      # Original user prompt