#!/usr/bin/env python3
"""
Test YarnGPT audio generation
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY")

if not YARNGPT_API_KEY:
    print("❌ YARNGPT_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {YARNGPT_API_KEY[:10]}...")

# Test text
test_text = "Ah ah! You wan tell me say Messi pass me? Abeg, make I show you why I be the real GOAT!"

print(f"\n🎤 Testing audio generation with text:")
print(f"   '{test_text}'")

url = "https://yarngpt.ai/api/v1/tts"
headers = {
    "Authorization": f"Bearer {YARNGPT_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "text": test_text,
    "voice": "Idera"
}

try:
    print("\n📡 Sending request to YarnGPT...")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        # Save test audio
        with open("test_audio.mp3", "wb") as f:
            f.write(response.content)
        print(f"✅ Audio generated successfully!")
        print(f"   Saved to: test_audio.mp3")
        print(f"   Size: {len(response.content)} bytes")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
