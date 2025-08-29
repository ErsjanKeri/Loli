from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from app.models.video import VideoRequest, VideoResponse, VideoStatus
from app.services.storage import VideoStorage, video_storage
from app.services.ai_orchestrator import AIOrchestrator
from app.services.video_processor import VideoProcessor
from app.api.dependencies import get_video_storage, get_script_generator, get_video_processor
from app.core.config import settings
from app.services.aws_polly import PollyService
import uuid
import logging
import os
import subprocess

logger = logging.getLogger(__name__)
router = APIRouter()


async def generate_video_task(
        video_id: str,
        prompt: str,
        model: str,
        voice: str,
        storage: VideoStorage,
        script_generator: AIOrchestrator,
        video_processor: VideoProcessor
):
    """Background task for video generation"""
    try:
        logger.info(f"[{video_id}] Starting video generation task")
        logger.debug(f"[{video_id}] Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        logger.debug(f"[{video_id}] Model: {model}, Voice: {voice}")

        # Update status: generating script
        logger.info(f"[{video_id}] Step 1/3: Generating explanation and script via pipeline")
        storage.update_video(
            video_id,
            status=VideoStatus.GENERATING_SCRIPT,
            message="Running LLM pipeline (explanation → refinement → script → validation)...",
            progress=25
        )

        logger.debug(f"[{video_id}] Calling AI Orchestrator pipeline with model: {model}...")
        script_content = await script_generator.generate_video_content(prompt, model)
        logger.info(f"[{video_id}] ✅ Pipeline produced script ({len(script_content)} chars)")
        logger.debug(f"[{video_id}] Script preview: {script_content[:200]}{'...' if len(script_content) > 200 else ''}")

        storage.update_video(video_id, script_content=script_content, progress=40)

        # Update status: rendering video
        logger.info(f"[{video_id}] Step 2/3: Starting video rendering")
        storage.update_video(
            video_id,
            status=VideoStatus.RENDERING_VIDEO,
            message="Rendering video...",
            progress=50
        )

        # Process video - now async with S3 upload
        logger.debug(f"[{video_id}] Calling video processor...")
        
        # Prepare metadata for S3
        video_metadata = {
            'original_question': prompt,
            'model_used': model,
            'voice_used': voice,
        }
        
        # Update status: uploading to S3
        storage.update_video(
            video_id,
            status=VideoStatus.UPLOADING_TO_S3,
            message="Uploading video to S3...",
            progress=85
        )
        
        video_path, s3_url = await video_processor.process_video(script_content, video_id, video_metadata)
        logger.info(f"[{video_id}] ✅ Video rendered successfully: {video_path}")

        # Determine final status based on S3 upload success
        if s3_url:
            final_status = VideoStatus.COMPLETED
            final_message = "Video generated and uploaded successfully"
            logger.info(f"[{video_id}] ✅ S3 upload successful: {s3_url}")
        else:
            final_status = VideoStatus.COMPLETED_WITHOUT_S3
            final_message = "Video generated successfully (S3 upload failed)"
            logger.warning(f"[{video_id}] ⚠️ S3 upload failed, but local video available")

        # Update status: completed
        logger.info(f"[{video_id}] Step 3/3: Finalizing")
        storage.update_video(
            video_id,
            status=final_status,
            message=final_message,
            video_path=video_path,
            s3_url=s3_url,
            progress=100
        )

        logger.info(f"[{video_id}] 🎉 Video generation completed successfully!")

    except Exception as e:
        logger.error(f"[{video_id}] ❌ Video generation failed: {e}")
        logger.exception(f"[{video_id}] Full traceback:")
        storage.update_video(
            video_id,
            status=VideoStatus.FAILED,
            message="Video generation failed",
            error_details=str(e)
        )


@router.post("/videos", response_model=VideoResponse)
async def create_video(
        request: VideoRequest,
        background_tasks: BackgroundTasks,
        storage: VideoStorage = Depends(get_video_storage),
        script_generator: AIOrchestrator = Depends(get_script_generator),
        video_processor: VideoProcessor = Depends(get_video_processor)
):
    """Generate educational video from prompt"""

    # Check if we've hit the concurrent limit
    if storage.get_active_video_count() >= settings.MAX_CONCURRENT_VIDEOS:
        raise HTTPException(
            status_code=429,
            detail="Maximum concurrent video generation limit reached. Please try again later."
        )

    video_id = str(uuid.uuid4())

    # Create video entry
    video_info = storage.create_video(video_id, request.prompt)

    # Start background task
    background_tasks.add_task(
        generate_video_task,
        video_id,
        request.prompt,
        request.model or "claude-3-7-sonnet",
        request.voice or "Joanna",
        storage,
        script_generator,
        video_processor
    )

    return VideoResponse(
        video_id=video_id,
        status=video_info.status,
        message=video_info.message,
        video_url=f"/api/v1/videos/{video_id}/status",
        created_at=video_info.created_at,
        progress=video_info.progress
    )


@router.get("/videos/{video_id}/status", response_model=VideoResponse)
async def get_video_status(
        video_id: str,
        storage: VideoStorage = Depends(get_video_storage)
):
    """Get video generation status"""
    video_info = storage.get_video(video_id)

    # Legacy video_url for backward compatibility
    video_url = None
    if video_info.status in [VideoStatus.COMPLETED, VideoStatus.COMPLETED_WITHOUT_S3]:
        video_url = f"/api/v1/videos/{video_id}/download"

    return VideoResponse(
        video_id=video_id,
        status=video_info.status,
        message=video_info.message,
        video_url=video_url,
        s3_url=video_info.s3_url,  # New S3 URL field
        created_at=video_info.created_at,
        progress=video_info.progress
    )


@router.get("/videos/{video_id}/download")
async def download_video(
        video_id: str,
        storage: VideoStorage = Depends(get_video_storage)
):
    """Download generated video (legacy endpoint - prefer S3 URL)"""
    video_info = storage.get_video(video_id)

    if video_info.status not in [VideoStatus.COMPLETED, VideoStatus.COMPLETED_WITHOUT_S3]:
        raise HTTPException(
            status_code=400,
            detail="Video is not ready for download"
        )

    if not video_info.video_path or not os.path.exists(video_info.video_path):
        raise HTTPException(
            status_code=404,
            detail="Video file not found"
        )

    return FileResponse(
        path=video_info.video_path,
        media_type='video/mp4',
        filename=f"educational_video_{video_id}.mp4"
    )


@router.get("/videos/{video_id}/script")
async def get_video_script(
        video_id: str,
        storage: VideoStorage = Depends(get_video_storage)
):
    """Get the generated Manim script for a video"""
    video_info = storage.get_video(video_id)

    if not video_info.script_content:
        raise HTTPException(
            status_code=404,
            detail="Script not available for this video"
        )

    return {
        "video_id": video_id,
        "script_content": video_info.script_content,
        "status": video_info.status
    }


@router.delete("/videos/{video_id}")
async def delete_video(
        video_id: str,
        storage: VideoStorage = Depends(get_video_storage)
):
    """Delete video"""
    success = storage.delete_video(video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")

    return {"message": "Video deleted successfully"}


@router.get("/videos")
async def list_videos(
        status: VideoStatus = None,
        storage: VideoStorage = Depends(get_video_storage)
):
    """List all videos, optionally filtered by status"""
    videos = storage.list_videos(status)

    return {
        "videos": [
            {
                "video_id": v.video_id,
                "status": v.status,
                "message": v.message,
                "created_at": v.created_at,
                "progress": v.progress,
                "download_url": f"/api/v1/videos/{v.video_id}/download" if v.status in [VideoStatus.COMPLETED, VideoStatus.COMPLETED_WITHOUT_S3] else None,
                "s3_url": v.s3_url
            }
            for v in videos
        ],
        "total": len(videos)
    }


@router.get("/stats")
async def get_stats(
        storage: VideoStorage = Depends(get_video_storage)
):
    """Get API statistics"""
    return storage.get_stats()


@router.post("/cleanup")
async def cleanup_old_videos(
        storage: VideoStorage = Depends(get_video_storage)
):
    """Manually trigger cleanup of old videos"""
    storage.cleanup_old_videos()
    return {"message": "Cleanup completed"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if Manim is installed
        result = subprocess.run(["manim", "--version"], capture_output=True, text=True, timeout=10)
        manim_version = result.stdout.strip() if result.returncode == 0 else "Not installed"

        # Check if ffmpeg is available
        ffmpeg_result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        ffmpeg_available = ffmpeg_result.returncode == 0

        return {
            "status": "healthy",
            "manim_version": manim_version,
            "ffmpeg_available": ffmpeg_available,
            "active_videos": video_storage.get_active_video_count(),
            "temp_dir": settings.TEMP_DIR,
            "videos_dir": settings.VIDEOS_DIR
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/models")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "bedrock_models": settings.BEDROCK_MODELS,
        "openai_models": ["gpt-5"],
        "all_models": settings.BEDROCK_MODELS + ["gpt-5"],
        "default_model": "claude-3-5-sonnet-v2"
    }


@router.get("/voices")
async def get_available_voices():
    """Get list of available voices"""
    try:
        polly = PollyService()
        return {
            "voices": polly.get_available_voices(),
            "available_voices": settings.AVAILABLE_VOICES,
            "default_voice": settings.DEFAULT_VOICE
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }