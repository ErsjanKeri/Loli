#!/usr/bin/env python3
"""
Final test after fixing IAM permissions
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.aws_bedrock import BedrockService

async def test_all_claude_models():
    print("🔧 Testing all Claude models after IAM fix...")
    
    bedrock = BedrockService()
    
    models_to_test = [
        'claude-3-5-sonnet-v2',
        'claude-sonnet-4'
    ]
    
    for model in models_to_test:
        try:
            print(f"\n🧪 Testing {model}...")
            result = await bedrock.generate_script(
                'Write a simple Python print statement', 
                model
            )
            
            print(f"✅ {model} SUCCESS!")
            print(f"📝 Response length: {len(result)} characters")
            
        except Exception as e:
            print(f"❌ {model} failed: {str(e)[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_all_claude_models())
