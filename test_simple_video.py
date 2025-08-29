#!/usr/bin/env python3
"""
Simple test with mock Polly to isolate Manim script issues
"""

import os
import sys
import tempfile
import shutil

# Create a simple test script that should work
SIMPLE_TEST_SCRIPT = '''
from manim import *

class TestScene(Scene):
    def construct(self):
        # Simple number
        number = Text("42", font_size=72, color=BLUE)
        number.move_to(ORIGIN)
        
        # Simple animation
        self.play(Write(number))
        
        # Simple circle - NO surround method, NO buffer parameter
        circle = Circle(radius=1.5, color=YELLOW, stroke_width=3)
        circle.move_to(ORIGIN)
        
        self.play(Create(circle))
        self.wait(2)
'''

def test_manim_only():
    """Test Manim script without any voiceover"""
    print("🎬 Testing simple Manim script...")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="manim_test_")
    script_path = os.path.join(temp_dir, "scene.py")
    
    try:
        # Write script
        with open(script_path, 'w') as f:
            f.write(SIMPLE_TEST_SCRIPT)
        
        # Run manim
        import subprocess
        cmd = [
            "manim",
            script_path,
            "TestScene",
            "-ql",
            "--disable_caching",
            f"--media_dir={temp_dir}/media"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Simple Manim script works!")
            
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
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_manim_only()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
