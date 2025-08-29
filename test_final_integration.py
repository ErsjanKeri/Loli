#!/usr/bin/env python3
"""
Test full video generation with the working GPT-5 script
"""

import sys
import os
import tempfile
import shutil
import asyncio

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Use the actual GPT-5 generated script from our test
WORKING_SCRIPT = '''from manim import *
from manim_voiceover import VoiceoverScene
from app.services.aws_polly import create_polly_service


class ShowNumber42(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            create_polly_service(
                voice="Joanna",
                style="friendly"
            )
        )
        
        # Create the number 42
        number = Text("42", font_size=96, color=BLUE)
        number.move_to(ORIGIN)
        
        # Add voiceover for introduction
        with self.voiceover(text="Here is the number forty-two") as tracker:
            self.play(Write(number), run_time=tracker.duration)
        
        # Create a circle around the number - CORRECT positioning
        circle = Circle(radius=1.5, color=YELLOW, stroke_width=4)
        circle.move_to(number.get_center())
        
        # Add voiceover for highlighting
        with self.voiceover(text="Let me highlight it with a circle") as tracker:
            self.play(Create(circle), run_time=tracker.duration - 0.5)
            self.wait(0.5)
        
        # Final pause
        self.wait(2)
'''

def test_full_video_generation():
    """Test complete video generation with working script"""
    print("🎬 Testing full video generation...")
    
    try:
        from services.video_processor import VideoProcessor
        
        print("   Creating video processor...")
        processor = VideoProcessor()
        
        print("   Processing video with working script...")
        video_id = "test_final"
        
        async def run_test():
            video_path = await processor.process_video(WORKING_SCRIPT, video_id)
            return video_path
        
        video_path = asyncio.run(run_test())
        
        print(f"   ✅ Video generated: {video_path}")
        
        # Check file
        if os.path.exists(video_path):
            size = os.path.getsize(video_path)
            print(f"   ✅ Video file exists ({size} bytes)")
            
            if size > 10000:  # At least 10KB
                print("   ✅ Video file has reasonable size")
                print("   🎉 FULL VIDEO GENERATION WORKS!")
                return True
            else:
                print("   ❌ Video file too small")
        else:
            print("   ❌ Video file not found")
            
        return False
        
    except Exception as e:
        print(f"   ❌ Video generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test the complete pipeline"""
    print("🚀 Testing complete video generation pipeline...")
    print("=" * 60)
    
    success = test_full_video_generation()
    
    if success:
        print("\n🎉 SUCCESS! Video generation is working end-to-end!")
        print("Ready to integrate back into the API!")
        return True
    else:
        print("\n❌ Video generation still has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
