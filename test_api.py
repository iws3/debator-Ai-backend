#!/usr/bin/env python3
"""
Test script to debug the Gemini API integration
Run this to test if your API key and setup work correctly
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

print("="*60)
print("🧪 Testing Gemini API Integration")
print("="*60)

# Test 1: Check API Key
print("\n1️⃣ Checking API Key...")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found in environment!")
    print("   Please check your .env file")
    exit(1)
else:
    print(f"✅ API Key found: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-5:]}")

# Test 2: Initialize Client
print("\n2️⃣ Initializing Gemini Client...")
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✅ Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Test 3: Test Text Generation
print("\n3️⃣ Testing Text Generation...")
try:
    prompt = "Say 'Hello from Nigeria!' in Nigerian Pidgin English (max 1 sentence)"
    print(f"   Prompt: {prompt}")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=100,
        )
    )
    
    print(f"\n   Response object type: {type(response)}")
    print(f"   Has 'text' attr: {hasattr(response, 'text')}")
    print(f"   Has 'candidates' attr: {hasattr(response, 'candidates')}")
    print(f"   Has 'parts' attr: {hasattr(response, 'parts')}")
    
    # Try to get text
    if hasattr(response, 'text') and response.text:
        result = response.text
        print(f"\n✅ Got text directly: {result}")
    elif hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        print(f"   Candidate type: {type(candidate)}")
        if hasattr(candidate, 'content'):
            content = candidate.content
            print(f"   Content type: {type(content)}")
            if hasattr(content, 'parts'):
                parts_text = []
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        parts_text.append(part.text)
                result = ' '.join(parts_text)
                print(f"\n✅ Extracted from candidates: {result}")
            else:
                print("❌ No parts in content")
        else:
            print("❌ No content in candidate")
    else:
        print("❌ No text or candidates in response")
        print(f"   Response: {response}")
        
except Exception as e:
    print(f"❌ Text generation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test Image Generation (optional)
print("\n4️⃣ Testing Image Generation...")
try:
    prompt = "A simple red circle on white background"
    print(f"   Prompt: {prompt}")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )
    )
    
    print(f"\n   Response object type: {type(response)}")
    print(f"   Has 'parts' attr: {hasattr(response, 'parts')}")
    print(f"   Has 'candidates' attr: {hasattr(response, 'candidates')}")
    
    image_found = False
    
    # Check response.parts
    if hasattr(response, 'parts') and response.parts:
        for i, part in enumerate(response.parts):
            print(f"   Part {i}: {type(part)}")
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"✅ Found image in parts! Size: {len(part.inline_data.data)} bytes")
                image_found = True
                break
    
    # Check candidates
    if not image_found and hasattr(response, 'candidates') and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"✅ Found image in candidates! Size: {len(part.inline_data.data)} bytes")
                        image_found = True
                        break
    
    if not image_found:
        print("⚠️  Image generation may not be supported yet")
        print(f"   Response structure: {dir(response)}")
        
except Exception as e:
    print(f"⚠️  Image generation not working (this is optional): {e}")

print("\n" + "="*60)
print("✅ Testing Complete!")
print("="*60)
print("\nIf text generation worked, your setup is good!")
print("If it didn't work, check:")
print("  1. Your API key is correct")
print("  2. You have billing enabled on Google AI Studio")
print("  3. The API is accessible from your location")