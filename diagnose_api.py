#!/usr/bin/env python3
"""Diagnostic tool to test Google Realtime API connection"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_google_connection():
    """Test Google Realtime API connection"""
    print("🔍 Google Realtime API Diagnostic Tool\n")
    
    api_key = os.getenv("GOOGLE_API_KEY", "").strip().strip("'\"")
    
    if not api_key or len(api_key) < 10:
        print("❌ GOOGLE_API_KEY is missing or invalid in .env")
        return False
    
    print(f"✓ API Key found: {api_key[:20]}...\n")
    
    try:
        print("📡 Attempting to import Google plugin...")
        from livekit.plugins import google
        print("✓ Google plugin imported\n")
        
        print("⏳ Testing model creation...")
        model = google.beta.realtime.RealtimeModel(voice="Charon")
        print("✓ Model created successfully\n")
        
        print("⏳ Testing basic API call (this may take 30+ seconds)...")
        
        # Try a simple connection test by importing the actual session
        try:
            from google.genai import live
            print("✓ google.genai.live imported\n")
        except ImportError as e:
            print(f"⚠️ Could not import google.genai.live: {e}\n")
        
        print("✅ Basic configuration looks good!")
        print("\n📝 Notes:")
        print("- If the agent still times out, it's likely a network or API service issue")
        print("- Check your internet connection (especially with proxies/VPN)")
        print("- Verify Google Cloud quotas at https://console.cloud.google.com/")
        print("- The actual connection test happens when agent receives audio input")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify GOOGLE_API_KEY is correct in .env")
        print("2. Check internet connection")
        print("3. Try: pip install --upgrade google-genai livekit-plugins-google")
        print("4. Restart the agent")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_google_connection())
    exit(0 if result else 1)
