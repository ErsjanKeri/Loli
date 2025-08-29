#!/usr/bin/env python3
"""
Test script for isolated video generation with AWS Polly
This allows us to test without API calls and debug systematically
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.aws_polly import create_polly_service
from services.video_processor import VideoProcessor
from core.config import settings

# Simple, working Manim script with Polly voiceover
TEST_SCRIPT = '''
from manim import *
from manim_voiceover import VoiceoverScene
from app.services.aws_polly import create_polly_service

class TestScene(VoiceoverScene):
    def construct(self):
        # Initialize speech service
        self.set_speech_service(
            create_polly_service(
                voice="Joanna",
                style="friendly"
            )
        )
        
        # Create simple number
        number = Text("42", font_size=72, color=BLUE)
        number.move_to(ORIGIN)
        
        # Add voiceover and animation
        with self.voiceover(text="Here is the number forty-two") as tracker:
            self.play(Write(number), run_time=tracker.duration)
        
        # Simple highlight without problematic methods
        highlight = Circle(radius=1.5, color=YELLOW, stroke_width=3)
        highlight.move_to(number.get_center())
        
        with self.voiceover(text="Let me highlight it with a circle") as tracker:
            self.play(Create(highlight), run_time=tracker.duration - 0.5)
            self.wait(0.5)
        
        # Final wait
        self.wait(2)
'''

def test_polly_service():
    """Test AWS Polly service in isolation"""
    print("🎤 Testing AWS Polly service...")
    
    try:
        polly = create_polly_service(voice="Joanna")
        result = polly.generate_from_text("This is a test")
        
        print(f"✅ Polly service working! Result type: {type(result)}")
        print(f"   Result: {result}")
        
        if isinstance(result, dict) and "original_audio" in result:
            print("✅ Polly returns correct dictionary format")
            return True
        else:
            print("❌ Polly returns incorrect format")
            return False
            
    except Exception as e:
        print(f"❌ Polly service failed: {e}")
        return False

def test_video_generation():
    """Test video generation with our test script"""
    print("🎬 Testing video generation...")
    
    try:
        # Create video processor
        processor = VideoProcessor()
        
        # Generate video with test script
        video_id = "test_video"
        
        print("   Running Manim with test script...")
        
        # Use asyncio to run the async function
        import asyncio
        
        async def run_test():
            video_path = await processor.process_video(TEST_SCRIPT, video_id)
            return video_path
        
        video_path = asyncio.run(run_test())
        
        print(f"✅ Video generated successfully: {video_path}")
        
        # Check if file exists and has content
        if os.path.exists(video_path) and os.path.getsize(video_path) > 1000:
            print(f"✅ Video file is valid ({os.path.getsize(video_path)} bytes)")
            return True
        else:
            print("❌ Video file is invalid or empty")
            return False
            
    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests systematically"""
    print("🚀 Starting systematic video generation testing...")
    print("=" * 60)
    
    # Test 1: Polly service
    polly_ok = test_polly_service()
    print()
    
    if not polly_ok:
        print("❌ Cannot proceed - Polly service is broken")
        return False
    
    # Test 2: Video generation
    video_ok = test_video_generation()
    print()
    
    if video_ok:
        print("🎉 ALL TESTS PASSED! Video generation is working!")
        return True
    else:
        print("❌ Video generation is still broken")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
