#!/usr/bin/env python3
"""
Quick test to verify the image processing endpoints are working
"""

import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Image Processing Endpoints")
    print("=" * 50)
    
    # Test 1: Generate image from prompt
    print("\n1. Testing image generation...")
    try:
        response = requests.post(f"{base_url}/api/images/generate", json={
            "prompt": "A beautiful solar panel farm in a green landscape"
        })
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: List generated images
    print("\n2. Testing image listing...")
    try:
        response = requests.get(f"{base_url}/api/images/list/generated")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Generated Images Count: {data.get('count', 0)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints()
