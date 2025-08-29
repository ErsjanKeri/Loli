#!/usr/bin/env python3
"""
Test voiceover with mock Polly service
"""

import os
import sys
import tempfile
import shutil

# Test script with working voiceover pattern
VOICEOVER_TEST_SCRIPT = '''
from manim import *
from manim_voiceover import VoiceoverScene
import tempfile
import os
import hashlib

# Mock Polly service for testing
class MockPollyService:
    def __init__(self, voice="Joanna", style="friendly", **kwargs):
        self.voice = voice
        self.cache_dir = tempfile.mkdtemp()
        
    def generate_from_text(self, text, cache_dir=None, **kwargs):
        """Return dictionary format expected by manim-voiceover"""
        import hashlib
        import tempfile
        
        # Create a dummy audio file (empty MP3)
        text_hash = hashlib.md5(f"{text}_{self.voice}".encode()).hexdigest()
        audio_file = os.path.join(self.cache_dir, f"mock_{text_hash}.mp3")
        
        # Create empty MP3 file
        if not os.path.exists(audio_file):
            with open(audio_file, 'wb') as f:
                # Write minimal MP3 header (silent audio)
                f.write(b'\\xff\\xfb\\x90\\x00')
        
        # Return correct dictionary format
        return {
            "original_audio": audio_file,
            "final_audio": os.path.basename(audio_file)
        }

def create_mock_polly_service(voice="Joanna", style="friendly"):
    return MockPollyService(voice=voice, style=style)

class TestVoiceoverScene(VoiceoverScene):
    def construct(self):
        # Initialize speech service with mock
        self.set_speech_service(create_mock_polly_service())
        
        # Simple number
        number = Text("42", font_size=72, color=BLUE)
        number.move_to(ORIGIN)
        
        # Add voiceover and animation
        with self.voiceover(text="Here is the number forty-two") as tracker:
            self.play(Write(number), run_time=tracker.duration)
        
        # Simple circle - CORRECT positioning
        circle = Circle(radius=1.5, color=YELLOW, stroke_width=3)
        circle.move_to(number.get_center())  # CORRECT: use move_to
        
        with self.voiceover(text="Let me highlight it with a circle") as tracker:
            self.play(Create(circle), run_time=tracker.duration - 0.5)
            self.wait(0.5)
        
        self.wait(2)
'''

def test_voiceover_mock():
    """Test voiceover with mock service"""
    print("🎤 Testing voiceover with mock Polly...")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="voiceover_test_")
    script_path = os.path.join(temp_dir, "scene.py")
    
    try:
        # Write script
        with open(script_path, 'w') as f:
            f.write(VOICEOVER_TEST_SCRIPT)
        
        # Run manim
        import subprocess
        cmd = [
            "manim",
            script_path,
            "TestVoiceoverScene",
            "-ql",
            "--disable_caching",
            f"--media_dir={temp_dir}/media"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Voiceover test works!")
            
            # Find generated video
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        video_path = os.path.join(root, file)
                        size = os.path.getsize(video_path)
                        print(f"✅ Video generated: {video_path} ({size} bytes)")
                        return True
            
            print("❌ No video file found")
            return False
        else:
            print(f"❌ Manim failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_voiceover_mock()
    print(f"\\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
