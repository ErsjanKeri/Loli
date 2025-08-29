from typing import Dict, Optional, List
from app.models.video import VideoInfo, VideoStatus
from app.core.config import settings
from app.core.exceptions import VideoNotFoundError
import os
import logging
from datetime import datetime, timedelta
import threading
import asyncio

logger = logging.getLogger(__name__)


class VideoStorage:
    def __init__(self):
        self._videos: Dict[str, VideoInfo] = {}
        self._lock = threading.Lock()
        self._s3_service = None
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    def _get_s3_service(self):
        """Get S3 service instance (lazy initialization)"""
        if self._s3_service is None:
            try:
                from app.services.s3_video_service import S3VideoService
                self._s3_service = S3VideoService()
            except Exception as e:
                logger.warning(f"Could not initialize S3 service: {e}")
                self._s3_service = None
        return self._s3_service

    def _s3_to_video_info(self, s3_video: dict) -> VideoInfo:
        """Convert S3 video data to VideoInfo object"""
        metadata = s3_video.get('metadata', {})
        
        # Convert offset-aware datetime to offset-naive UTC
        created_at = s3_video['last_modified']
        if hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        
        return VideoInfo(
            video_id=s3_video['video_id'],
            status=VideoStatus.COMPLETED,  # Assume completed since it exists in S3
            message="Video completed",
            s3_url=s3_video['s3_url'],
            created_at=created_at,
            prompt=metadata.get('original-question', f"Video {s3_video['video_id'][:8]}"),
            progress=100
        )

    def create_video(self, video_id: str, prompt: str) -> VideoInfo:
        """Create a new video entry"""
        with self._lock:
            video_info = VideoInfo(
                video_id=video_id,
                status=VideoStatus.QUEUED,
                message="Video generation queued",
                created_at=datetime.utcnow(),
                prompt=prompt
            )
            self._videos[video_id] = video_info
            return video_info

    def get_video(self, video_id: str) -> VideoInfo:
        """Get video information"""
        with self._lock:
            # First check in-memory storage
            if video_id in self._videos:
                return self._videos[video_id]
            
            # If not in memory, check S3 using synchronous method
            try:
                s3_service = self._get_s3_service()
                if s3_service:
                    s3_videos = s3_service._list_videos_sync()  # Use synchronous method
                    for s3_video in s3_videos:
                        if s3_video['video_id'] == video_id:
                            # Convert S3 video to VideoInfo and return
                            return self._s3_to_video_info(s3_video)
            except Exception as e:
                logger.warning(f"Failed to check S3 for video {video_id}: {e}")
            
            # Video not found in memory or S3
            raise VideoNotFoundError(f"Video {video_id} not found")

    def update_video(self, video_id: str, **updates) -> VideoInfo:
        """Update video information"""
        with self._lock:
            # Don't call self.get_video() - do the check directly here
            if video_id not in self._videos:
                raise VideoNotFoundError(f"Video {video_id} not found")

            video_info = self._videos[video_id]
            for key, value in updates.items():
                if hasattr(video_info, key):
                    setattr(video_info, key, value)
            return video_info

    def delete_video(self, video_id: str) -> bool:
        """Delete video and associated files"""
        with self._lock:
            try:
                video_info = self.get_video(video_id)

                # Remove video file if exists
                if video_info.video_path and os.path.exists(video_info.video_path):
                    os.remove(video_info.video_path)
                    logger.info(f"Deleted video file: {video_info.video_path}")

                # Remove from memory
                del self._videos[video_id]
                return True

            except VideoNotFoundError:
                return False

    async def list_videos(self, status: Optional[VideoStatus] = None) -> List[VideoInfo]:
        """List all videos from memory and S3, optionally filtered by status"""
        with self._lock:
            # Get videos from memory
            memory_videos = list(self._videos.values())
            memory_video_ids = {v.video_id for v in memory_videos}
        
        # Get videos from S3
        s3_videos = []
        s3_service = self._get_s3_service()
        if s3_service:
            try:
                s3_video_data = await s3_service.list_all_videos()
                for s3_video in s3_video_data:
                    # Only add S3 videos that aren't already in memory
                    if s3_video['video_id'] not in memory_video_ids:
                        s3_videos.append(self._s3_to_video_info(s3_video))
            except Exception as e:
                logger.error(f"Failed to fetch S3 videos: {e}")
        
        # Combine memory and S3 videos
        all_videos = memory_videos + s3_videos
        
        # Apply status filter if specified
        if status:
            all_videos = [v for v in all_videos if v.status == status]
        
        # Sort videos by created_at with error handling
        try:
            return sorted(all_videos, key=lambda x: x.created_at, reverse=True)
        except TypeError as e:
            logger.error(f"Error sorting videos by created_at: {e}")
            # Fallback: sort by video_id if datetime comparison fails
            return sorted(all_videos, key=lambda x: x.video_id, reverse=True)

    def cleanup_old_videos(self):
        """Clean up videos older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.VIDEO_RETENTION_DAYS)
        videos_to_delete = []

        with self._lock:
            videos_to_delete = [
                video_id for video_id, video_info in self._videos.items()
                if video_info.created_at < cutoff_date
            ]

        for video_id in videos_to_delete:
            self.delete_video(video_id)
            logger.info(f"Cleaned up old video: {video_id}")

    def get_active_video_count(self) -> int:
        """Get count of videos currently being processed"""
        with self._lock:
            active_statuses = {VideoStatus.QUEUED, VideoStatus.GENERATING_SCRIPT, VideoStatus.RENDERING_VIDEO, VideoStatus.UPLOADING_TO_S3}
            return sum(1 for v in self._videos.values() if v.status in active_statuses)

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        with self._lock:
            total_videos = len(self._videos)
            status_counts = {}
            for status in VideoStatus:
                status_counts[status.value] = sum(1 for v in self._videos.values() if v.status == status)

            return {
                "total_videos": total_videos,
                "active_videos": self.get_active_video_count(),
                "status_breakdown": status_counts
            }


# Global storage instance
video_storage = VideoStorage()