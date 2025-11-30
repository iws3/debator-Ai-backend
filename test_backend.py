#!/usr/bin/env python3
"""
Quick test script to verify the debate backend is working correctly
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000"

def test_health_check():
    """Test the root endpoint"""
    print("\n" + "="*50)
    print("🏥 Testing Health Check...")
    print("="*50)
    
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_image_generation():
    """Test GOAT image generation"""
    print("\n" + "="*50)
    print("🎨 Testing Image Generation...")
    print("="*50)
    
    try:
        response = requests.post(
            f"{API_URL}/generate-goat-image",
            json={"goat_name": "Messi", "domain": "Sports"},
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if "imageUrl" in data:
            image_type = "base64" if data["imageUrl"].startswith("data:") else "URL"
            print(f"✅ Image generated ({image_type})")
            print(f"Image URL length: {len(data['imageUrl'])} characters")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_start_debate():
    """Test starting a debate"""
    print("\n" + "="*50)
    print("🥊 Testing Start Debate...")
    print("="*50)
    
    try:
        response = requests.post(
            f"{API_URL}/start-goat-debate",
            json={
                "user_goat": "Messi",
                "ai_goat": "Ronaldo",
                "domain": "Football"
            },
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if "debate_id" in data:
            print(f"\n✅ Debate started!")
            print(f"Debate ID: {data['debate_id']}")
            print(f"AI Opening: {data['ai_text']}")
            return data['debate_id']
        
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_debate_turn(debate_id):
    """Test a debate turn"""
    print("\n" + "="*50)
    print("💬 Testing Debate Turn...")
    print("="*50)
    
    try:
        response = requests.post(
            f"{API_URL}/debate-turn",
            json={
                "debate_id": debate_id,
                "user_text": "Messi has won more Ballon d'Ors than anyone in history!"
            },
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if "ai_text" in data:
            print(f"\n✅ Turn completed!")
            print(f"AI Response: {data['ai_text']}")
            print(f"Scores - User: {data.get('user_score', 0)}, AI: {data.get('ai_score', 0)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "🎭"*25)
    print("GOAT Debate Backend Test Suite")
    print("🎭"*25)
    
    # Check if backend is running
    print("\n⚠️  Make sure the backend is running on http://localhost:8000")
    print("   Run: cd backend && python main.py")
    input("\nPress Enter to start tests...")
    
    results = {
        "health_check": False,
        "image_generation": False,
        "start_debate": False,
        "debate_turn": False
    }
    
    # Test 1: Health Check
    results["health_check"] = test_health_check()
    
    # Test 2: Image Generation
    results["image_generation"] = test_image_generation()
    
    # Test 3: Start Debate
    debate_id = test_start_debate()
    results["start_debate"] = debate_id is not None
    
    # Test 4: Debate Turn (only if debate started)
    if debate_id:
        results["debate_turn"] = test_debate_turn(debate_id)
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Your backend is ready!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nCommon issues:")
        print("- Backend not running")
        print("- Missing API keys in .env")
        print("- Network/firewall issues")

if __name__ == "__main__":
    main()
