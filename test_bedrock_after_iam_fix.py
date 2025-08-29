#!/usr/bin/env python3
"""
Test script to verify Bedrock access after IAM permissions fix
Run this after updating IAM permissions
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.aws_bedrock import BedrockService

async def test_claude_sonnet_4_after_iam_fix():
    print("🔧 Testing Claude Sonnet 4 after IAM permissions fix...")
    
    bedrock = BedrockService()
    
    try:
        result = await bedrock.generate_script(
            'Create a simple Manim script that shows the number 42', 
            'claude-sonnet-4'
        )
        
        print("✅ SUCCESS! Claude Sonnet 4 is now working!")
        print(f"📝 Generated script length: {len(result)} characters")
        print(f"📝 First 300 chars: {result[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Still failing: {e}")
        
        if "AccessDenied" in str(e):
            print("\n💡 IAM permissions still need to be updated.")
            print("   Make sure you've added the bedrock:InvokeModel permission")
            print("   for inference profiles to your IAM user.")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_claude_sonnet_4_after_iam_fix())
    
    if success:
        print("\n🎉 Ready to use Claude Sonnet 4 in your video generation!")
        print("   You can now use 'claude-sonnet-4' as a model in your API calls.")
    else:
        print("\n🔧 Please fix the IAM permissions and try again.")
