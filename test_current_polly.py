#!/usr/bin/env python3
"""
Test current Polly service with proper credentials
"""

import sys
import os
import tempfile

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_polly_return_format():
    """Test that Polly returns correct dictionary format"""
    print("🎤 Testing Polly service return format...")
    
    try:
        from services.aws_polly import create_polly_service
        
        print("   Creating Polly service...")
        polly = create_polly_service(voice="Joanna")
        
        print("   Testing generate_from_text...")
        result = polly.generate_from_text("Test speech")
        
        print(f"   Result type: {type(result)}")
        print(f"   Result: {result}")
        
        if isinstance(result, dict):
            print("   ✅ Returns dictionary")
            if "original_audio" in result:
                print("   ✅ Has original_audio key")
                if "final_audio" in result:
                    print("   ✅ Has final_audio key")
                    print("   ✅ Polly service format is CORRECT!")
                    return True
                else:
                    print("   ❌ Missing final_audio key")
            else:
                print("   ❌ Missing original_audio key")
        else:
            print("   ❌ Returns wrong type (should be dict)")
            
        return False
        
    except Exception as e:
        print(f"   ❌ Polly test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_gpt5_generation():
    """Test GPT-5 script generation with new prompts"""
    print("🤖 Testing GPT-5 script generation...")
    
    try:
        from services.ai_orchestrator import AIOrchestrator
        
        print("   Creating AI Orchestrator...")
        orchestrator = AIOrchestrator()
        
        print("   Generating script with GPT-5...")
        import asyncio
        
        async def test_generation():
            script = await orchestrator.generate_script("Show the number 42", "gpt-5")
            return script
        
        script = asyncio.run(test_generation())
        
        print(f"   Generated script length: {len(script)} chars")
        
        # Check for problematic patterns
        if ".surround(" in script:
            print("   ❌ Script still contains .surround() method")
            return False
        
        if "buffer=" in script:
            print("   ❌ Script still contains buffer parameter")
            return False
            
        if "from app.services.aws_polly import" in script:
            print("   ✅ Script uses correct Polly import")
        else:
            print("   ❌ Script missing Polly import")
            return False
            
        print("   ✅ GPT-5 script generation looks good!")
        print(f"   Script preview: {script[:200]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ GPT-5 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run focused tests"""
    print("🔧 Testing individual components...")
    print("=" * 50)
    
    # Test 1: Polly format
    polly_ok = test_polly_return_format()
    print()
    
    # Test 2: GPT-5 generation
    gpt5_ok = test_simple_gpt5_generation()
    print()
    
    if polly_ok and gpt5_ok:
        print("🎉 ALL COMPONENT TESTS PASSED!")
        print("Ready to test full video generation...")
        return True
    else:
        print("❌ Some components are still broken")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
