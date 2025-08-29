import subprocess
import tempfile
import shutil
import os
import re
from app.core.config import settings
from app.core.exceptions import VideoProcessingError
import logging
import asyncio
import concurrent.futures
import platform

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        self.videos_dir = settings.VIDEOS_DIR
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

        # Fix temp directory for Windows
        if platform.system() == "Windows":
            self.temp_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "manim_videos")

        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)

    async def process_video(self, script_content: str, video_id: str) -> str:
        """Process Manim script and generate video"""
        temp_dir = None
        try:
            # Create temporary directory with proper path handling
            temp_dir = tempfile.mkdtemp(
                prefix=f"manim_{video_id}_",
                dir=self.temp_dir
            )
            temp_dir = os.path.normpath(temp_dir)  # Normalize path separators

            logger.info(f"📁 Created temp directory: {temp_dir}")
            logger.debug(f"Script content length: {len(script_content)} chars")

            # Generate video - run in executor to avoid blocking
            logger.info(f"🎬 Starting Manim rendering...")
            loop = asyncio.get_event_loop()

            import time
            start_time = time.time()
            video_path = await loop.run_in_executor(
                self.executor,
                self._run_manim,
                script_content,
                temp_dir,
                video_id
            )
            render_duration = time.time() - start_time
            logger.info(f"✅ Manim rendering completed in {render_duration:.2f}s")

            # Move to permanent location
            logger.debug(f"Moving video from {video_path} to permanent location...")
            final_path = self._move_to_permanent_location(video_path, video_id)

            logger.info(f"🎉 Video processing completed: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"❌ Video processing failed: {e}")
            logger.exception(f"Full video processing traceback:")
            raise VideoProcessingError(
                "Failed to process video",
                details=str(e)
            )
        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                logger.debug(f"🧹 Cleaning up temp directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"✅ Temp directory cleaned up")

    def _run_manim(self, script_content: str, temp_dir: str, video_id: str) -> str:
        """Execute Manim script"""
        logger.debug(f"[Thread] Starting Manim execution in {temp_dir}")

        script_path = os.path.join(temp_dir, "scene.py")

        # Write script to file
        logger.debug(f"[Thread] Writing script to {script_path}")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        logger.debug(f"[Thread] Script file written ({len(script_content)} chars)")
        
        # Copy required services to temp directory for local imports
        self._copy_services_to_temp(temp_dir, script_content)

        # Extract scene class name
        scene_class = self._extract_scene_class(script_content)
        logger.debug(f"[Thread] Extracted scene class: {scene_class}")

        # Create output directory
        output_dir = os.path.join(temp_dir, "media")
        os.makedirs(output_dir, exist_ok=True)

        # Build Manim command - simplified and more compatible
        cmd = [
            "manim",
            script_path,
            scene_class,
            "-ql",  # Low quality for faster rendering
            "--disable_caching",
            f"--media_dir={output_dir}",
        ]

        # Skip verbose mode to avoid Manim CLI issues

        logger.info(f"[Thread] 🎬 Executing Manim: {' '.join(cmd)}")

        # Set up environment
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # AWS settings for Polly
        env['AWS_ACCESS_KEY_ID'] = settings.AWS_ACCESS_KEY_ID
        env['AWS_SECRET_ACCESS_KEY'] = settings.AWS_SECRET_ACCESS_KEY
        env['AWS_REGION'] = settings.AWS_REGION
        if platform.system() == "Windows":
            env['PYTHONPATH'] = os.pathsep.join([temp_dir] + env.get('PYTHONPATH', '').split(os.pathsep))
        else:
            env['LANG'] = 'en_US.UTF-8'

        try:
            import time
            start_time = time.time()

            # Use a shorter timeout for initial testing
            timeout = min(settings.MANIM_PROCESSING_TIMEOUT, 300)  # Max 5 minutes for testing

            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                env=env
            )

            execution_time = time.time() - start_time
            logger.info(f"[Thread] ⏱️ Manim subprocess completed in {execution_time:.2f}s")
            logger.debug(f"[Thread] Return code: {result.returncode}")

            # Always log stdout and stderr for debugging
            if result.stdout:
                logger.info(f"[Thread] STDOUT: {result.stdout}")
            if result.stderr:
                logger.warning(f"[Thread] STDERR: {result.stderr}")

            if result.returncode != 0:
                logger.error(f"[Thread] ❌ Manim failed with return code {result.returncode}")
                raise VideoProcessingError(f"Manim execution failed: {result.stderr}")

            logger.info(f"[Thread] ✅ Manim completed successfully")

        except subprocess.TimeoutExpired:
            logger.error(f"[Thread] ⏰ Manim process timed out after {timeout}s")
            raise VideoProcessingError("Video generation timed out")
        except Exception as e:
            logger.error(f"[Thread] ❌ Unexpected error during Manim execution: {e}")
            raise

        # Find generated video
        logger.debug(f"[Thread] Searching for generated video file...")
        video_path = self._find_generated_video(temp_dir)
        logger.info(f"[Thread] 🎯 Found video file: {video_path}")
        return video_path

    def _copy_services_to_temp(self, temp_dir: str, script_content: str):
        """Copy required service files to temp directory for local imports"""
        if 'from app.services.aws_polly import' not in script_content:
            return  # No Polly service needed
        
        logger.debug(f"[Thread] Copying AWS Polly service to temp directory...")
        
        # Create app/services directory structure in temp
        app_dir = os.path.join(temp_dir, "app")
        services_dir = os.path.join(app_dir, "services")
        os.makedirs(services_dir, exist_ok=True)
        
        # Create __init__.py files for proper module structure
        with open(os.path.join(app_dir, "__init__.py"), 'w') as f:
            f.write("")
        with open(os.path.join(services_dir, "__init__.py"), 'w') as f:
            f.write("")
        
        # Copy aws_polly.py
        import shutil
        source_polly = os.path.join(os.path.dirname(__file__), "aws_polly.py")
        dest_polly = os.path.join(services_dir, "aws_polly.py")
        
        if os.path.exists(source_polly):
            shutil.copy2(source_polly, dest_polly)
            logger.debug(f"[Thread] ✅ Copied aws_polly.py to {dest_polly}")
        else:
            logger.warning(f"[Thread] ⚠️ Source file not found: {source_polly}")
        
        # Copy config.py (needed by aws_polly.py)
        source_config = os.path.join(os.path.dirname(__file__), "..", "core", "config.py")
        core_dir = os.path.join(app_dir, "core")
        os.makedirs(core_dir, exist_ok=True)
        with open(os.path.join(core_dir, "__init__.py"), 'w') as f:
            f.write("")
        
        dest_config = os.path.join(core_dir, "config.py")
        if os.path.exists(source_config):
            shutil.copy2(source_config, dest_config)
            logger.debug(f"[Thread] ✅ Copied config.py to {dest_config}")
        else:
            logger.warning(f"[Thread] ⚠️ Config file not found: {source_config}")

    def _extract_scene_class(self, script_content: str) -> str:
        """Extract scene class name from script"""
        # Look for class definition that inherits from Scene or VoiceoverScene
        patterns = [
            r'class\s+(\w+)\s*\([^)]*(?:Voiceover)?Scene[^)]*\):',
            r'class\s+(\w+)\s*\([^)]*Scene[^)]*\):',
            r'class\s+(\w*Scene\w*)\s*\([^)]*\):'
        ]

        for pattern in patterns:
            match = re.search(pattern, script_content)
            if match:
                return match.group(1)

        # Default fallback
        logger.warning("Could not extract scene class name, using default")
        return "Scene"

    def _find_generated_video(self, temp_dir: str) -> str:
        """Find the generated video file"""
        logger.debug(f"[Thread] Searching for video files in: {temp_dir}")

        # Search for MP4 files in the entire temp directory
        for root, dirs, files in os.walk(temp_dir):
            logger.debug(f"[Thread] Checking directory: {root}")
            logger.debug(f"[Thread] Files found: {files}")

            for file in files:
                if file.endswith('.mp4'):
                    video_path = os.path.join(root, file)
                    file_size = os.path.getsize(video_path)
                    logger.info(f"[Thread] Found video: {video_path} ({file_size} bytes)")

                    # Ensure the file is not empty
                    if file_size > 1000:  # At least 1KB
                        return video_path

        # List all files for debugging
        logger.error(f"[Thread] No valid video file found. Directory structure:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            logger.error(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                logger.error(f"{subindent}{file} ({file_size} bytes)")

        raise VideoProcessingError("No video file generated by Manim")

    def _move_to_permanent_location(self, temp_path: str, video_id: str) -> str:
        """Move video to permanent storage"""
        # Ensure videos directory exists
        os.makedirs(self.videos_dir, exist_ok=True)

        final_path = os.path.join(self.videos_dir, f"{video_id}.mp4")
        final_path = os.path.normpath(final_path)

        shutil.copy2(temp_path, final_path)

        # Verify the file was copied successfully
        if not os.path.exists(final_path):
            raise VideoProcessingError("Failed to copy video to permanent location")

        logger.info(f"Video moved to permanent location: {final_path}")
        return final_path

    def get_video_info(self, video_path: str) -> dict:
        """Get video file information"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", video_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                logger.warning(f"Could not get video info for {video_path}")
                return {}
        except Exception as e:
            logger.warning(f"Error getting video info: {e}")
            return {}