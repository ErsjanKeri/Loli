#!/usr/bin/env python3
"""
AWS Polly Setup Test Script

This script tests if your AWS credentials and Polly permissions are working correctly.
"""

import boto3
import os
from dotenv import load_dotenv

def test_aws_polly_setup():
    """Test AWS Polly setup and permissions"""
    
    print("🔥 AWS Polly Setup Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('app/.env')
    
    # Check credentials
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"✅ AWS_ACCESS_KEY_ID: {access_key[:20] if access_key else 'NOT FOUND'}...")
    print(f"✅ AWS_SECRET_ACCESS_KEY: {'*' * 20 if secret_key else 'NOT FOUND'}...")
    print(f"✅ AWS_REGION: {region}")
    print()
    
    if not access_key or not secret_key:
        print("❌ AWS credentials not found in .env file!")
        return False
    
    try:
        # Test basic AWS connectivity
        print("🔍 Testing AWS connectivity...")
        client = boto3.client(
            'polly',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Test 1: List available voices
        print("🎤 Testing Polly permissions - listing voices...")
        voices_response = client.describe_voices(LanguageCode='en-US')
        voices = [voice['Id'] for voice in voices_response['Voices'][:5]]
        print(f"✅ Found {len(voices_response['Voices'])} voices. Sample: {voices}")
        print()
        
        # Test 2: Try to synthesize a simple phrase
        print("🗣️ Testing speech synthesis...")
        test_text = "Hello, this is a test of AWS Polly integration."
        
        response = client.synthesize_speech(
            Text=test_text,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        
        # Save test audio
        with open('polly_test.mp3', 'wb') as f:
            f.write(response['AudioStream'].read())
        
        print(f"✅ Speech synthesis successful! Audio saved as 'polly_test.mp3'")
        print(f"   File size: {os.path.getsize('polly_test.mp3')} bytes")
        print()
        
        print("🎉 AWS Polly setup is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ AWS Polly test failed: {str(e)}")
        print()
        
        # Provide troubleshooting guidance
        if "UnrecognizedClientException" in str(e):
            print("🔧 SOLUTION: Your AWS credentials appear to be invalid.")
            print("   1. Check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            print("   2. Make sure they're correctly set in app/.env")
            print("   3. Verify the IAM user exists and is active")
            
        elif "AccessDenied" in str(e) or "not authorized" in str(e):
            print("🔧 SOLUTION: Your IAM user doesn't have Polly permissions.")
            print("   1. Go to AWS Console > IAM > Users > Your User")
            print("   2. Attach policy: 'AmazonPollyFullAccess'")
            print("   3. Or create custom policy with polly:* permissions")
            
        else:
            print("🔧 TROUBLESHOOTING:")
            print("   1. Check your internet connection")
            print("   2. Verify AWS region is correct")
            print("   3. Try regenerating your AWS access keys")
        
        return False

if __name__ == "__main__":
    success = test_aws_polly_setup()
    exit(0 if success else 1)
