"""
AWS S3 Video Upload Service

This service handles uploading generated videos to S3 with metadata
and provides public URLs for video access.
"""

import boto3
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings
from app.core.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class S3UploadError(VideoProcessingError):
    """Specific exception for S3 upload failures"""
    pass


class S3VideoService:
    """
    AWS S3 service for uploading videos with metadata and generating public URLs.
    
    Follows the same async patterns as other services in the project.
    """
    
    def __init__(self):
        """Initialize S3 client with existing AWS credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.region = settings.S3_REGION
            
            logger.info(f"🪣 S3VideoService initialized - Bucket: {self.bucket_name}, Region: {self.region}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3VideoService: {e}")
            raise S3UploadError(f"S3 service initialization failed: {str(e)}")

    async def upload_video(self, video_path: str, video_id: str, metadata: Dict) -> str:
        """
        Upload video to S3 with metadata and return public URL.
        
        Args:
            video_path: Local path to the video file
            video_id: Unique video identifier
            metadata: Video metadata including question, model, voice, etc.
            
        Returns:
            Public S3 URL for the uploaded video
            
        Raises:
            S3UploadError: If upload fails
        """
        try:
            logger.info(f"📤 Starting S3 upload for video {video_id}")
            
            # Verify local file exists
            if not os.path.exists(video_path):
                raise S3UploadError(f"Local video file not found: {video_path}")
                
            file_size = os.path.getsize(video_path)
            logger.debug(f"📁 Video file size: {file_size} bytes")
            
            # S3 key (filename in bucket)
            s3_key = f"{video_id}.mp4"
            
            # Format metadata for S3
            s3_metadata = self._format_metadata(metadata)
            
            # Upload to S3 (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._upload_file_sync,
                video_path,
                s3_key,
                s3_metadata
            )
            
            # Generate public URL
            public_url = self.get_public_url(video_id)
            
            logger.info(f"✅ S3 upload completed successfully for {video_id}")
            logger.info(f"🔗 Public URL: {public_url}")
            
            return public_url
            
        except S3UploadError:
            # Re-raise S3 specific errors
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during S3 upload: {e}")
            raise S3UploadError(f"S3 upload failed: {str(e)}")

    def _upload_file_sync(self, video_path: str, s3_key: str, metadata: Dict) -> None:
        """
        Synchronous S3 upload (runs in executor).
        
        Args:
            video_path: Local path to video file
            s3_key: S3 object key
            metadata: S3 metadata dictionary
        """
        try:
            import time
            start_time = time.time()
            
            self.s3_client.upload_file(
                video_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'Metadata': metadata
                    # No ACL - rely on bucket policy for public access
                }
            )
            
            upload_duration = time.time() - start_time
            logger.debug(f"🚀 S3 upload completed in {upload_duration:.2f}s")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"❌ S3 ClientError ({error_code}): {e}")
            raise S3UploadError(f"S3 upload failed: {error_code} - {str(e)}")
        except BotoCoreError as e:
            logger.error(f"❌ S3 BotoCoreError: {e}")
            raise S3UploadError(f"S3 connection error: {str(e)}")

    def _format_metadata(self, metadata: Dict) -> Dict[str, str]:
        """
        Format metadata for S3 storage.
        
        S3 metadata values must be strings and follow naming conventions.
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Formatted metadata for S3
        """
        formatted = {}
        
        # Map metadata fields to S3-compatible format
        field_mapping = {
            'original_question': 'original-question',
            'model_used': 'model-used', 
            'voice_used': 'voice-used',
            'generation_date': 'generation-date'
        }
        
        for key, value in metadata.items():
            # Use mapped key or original key
            s3_key = field_mapping.get(key, key.replace('_', '-'))
            
            # Convert value to string
            if isinstance(value, str):
                formatted[s3_key] = value
            elif value is not None:
                formatted[s3_key] = str(value)
                
        # Add current timestamp if not provided
        if 'generation-date' not in formatted:
            formatted['generation-date'] = datetime.utcnow().isoformat()
            
        logger.debug(f"📋 S3 metadata: {formatted}")
        return formatted

    def get_public_url(self, video_id: str) -> str:
        """
        Generate public S3 URL for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Public S3 URL
        """
        s3_key = f"{video_id}.mp4"
        public_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
        
        logger.debug(f"🔗 Generated public URL: {public_url}")
        return public_url

    async def verify_upload(self, video_id: str) -> bool:
        """
        Verify that a video was successfully uploaded to S3.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if video exists in S3, False otherwise
        """
        try:
            s3_key = f"{video_id}.mp4"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._check_object_exists,
                s3_key
            )
            
            logger.debug(f"✅ Verified S3 upload for {video_id}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not verify S3 upload for {video_id}: {e}")
            return False

    def _check_object_exists(self, s3_key: str) -> None:
        """Check if S3 object exists (raises exception if not)"""
        self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)

    async def delete_video(self, video_id: str) -> bool:
        """
        Delete video from S3.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            s3_key = f"{video_id}.mp4"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._delete_object_sync,
                s3_key
            )
            
            logger.info(f"🗑️ Deleted video {video_id} from S3")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not delete video {video_id} from S3: {e}")
            return False

    def _delete_object_sync(self, s3_key: str) -> None:
        """Synchronous S3 object deletion"""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
