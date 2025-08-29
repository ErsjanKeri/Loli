#!/usr/bin/env python3
"""
Test Claude Sonnet 4 after enabling model access in Bedrock console
Run this after enabling model access in AWS Console
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.aws_bedrock import BedrockService

async def test_claude_after_model_access():
    print("🔧 Testing Claude Sonnet 4 after enabling model access in console...")
    
    bedrock = BedrockService()
    
    try:
        # Simple test first
        result = await bedrock.generate_script(
            'Write a simple Python print statement that says hello world', 
            'claude-sonnet-4'
        )
        
        print("✅ SUCCESS! Claude Sonnet 4 is working!")
        print(f"📝 Response: {result[:200]}...")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Still failing: {error_msg}")
        
        if "AccessDenied" in error_msg:
            print("\n💡 Model access still not enabled.")
            print("   Go to AWS Console → Bedrock → Model Access")
            print("   Find 'Claude Sonnet 4' and enable it")
        elif "ValidationException" in error_msg:
            print("\n💡 Model access might be pending approval")
            print("   Wait a few more minutes and try again")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_claude_after_model_access())
    
    if success:
        print("\n🎉 Claude Sonnet 4 is ready!")
        print("   You can now use it in your video generation API")
    else:
        print("\n🔧 Please enable model access in AWS Console and try again")
