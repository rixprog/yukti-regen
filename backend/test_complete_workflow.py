#!/usr/bin/env python3
"""
Test the complete image processing workflow with sequential naming
"""

import os
import requests
from PIL import Image
import uuid
from datetime import datetime

def create_test_image():
    """Create a test image for processing"""
    os.makedirs("uploaded_images", exist_ok=True)
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color='red')
    
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 100), "ORIGINAL", fill='white', font=font)
    
    filename = f"test_original_{uuid.uuid4()}.jpg"
    filepath = os.path.join("uploaded_images", filename)
    img.save(filepath, 'JPEG', quality=95)
    
    print(f"✅ Created test image: {filepath}")
    return filepath

def test_image_processing():
    """Test the complete image processing workflow"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Complete Image Processing Workflow")
    print("=" * 60)
    
    # Create test image
    test_image_path = create_test_image()
    
    # Test 1: Process image with AI
    print("\n1. Testing image processing...")
    try:
        with open(test_image_path, 'rb') as f:
            files = {'image_file': f}
            data = {'prompt': 'Make this image more colorful and artistic'}
            
            response = requests.post(f"{base_url}/api/images/process", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Image processing successful")
                print(f"   Generated {result.get('count', 0)} images")
                print(f"   Edit numbers: {result.get('edit_numbers', [])}")
                
                for img in result.get('generated_images', []):
                    print(f"   - {img['filename']} (Edit #{img.get('edit_number', 'N/A')})")
                    print(f"     URL: {img['url']}")
            else:
                print(f"❌ Image processing failed: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Image processing error: {e}")
    
    # Test 2: Get edit count
    print("\n2. Testing edit count...")
    try:
        response = requests.get(f"{base_url}/api/images/edits/count")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Edit count: {data.get('edit_count', 0)}")
        else:
            print(f"❌ Edit count failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Edit count error: {e}")
    
    # Test 3: Get all edits
    print("\n3. Testing all edits...")
    try:
        response = requests.get(f"{base_url}/api/images/edits/all")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All edits: {data.get('count', 0)} images")
            for img in data.get('images', []):
                print(f"   - {img['filename']} (Edit #{img.get('edit_number', 'N/A')})")
        else:
            print(f"❌ All edits failed: {response.status_code}")
    except Exception as e:
        print(f"❌ All edits error: {e}")
    
    # Test 4: Test image URLs
    print("\n4. Testing image URLs...")
    try:
        response = requests.get(f"{base_url}/api/images/edits/all")
        if response.status_code == 200:
            data = response.json()
            for img in data.get('images', []):
                url = f"{base_url}{img['url']}"
                print(f"Testing: {url}")
                
                img_response = requests.get(url)
                if img_response.status_code == 200:
                    print(f"✅ {img['filename']}: OK ({len(img_response.content)} bytes)")
                else:
                    print(f"❌ {img['filename']}: Failed ({img_response.status_code})")
    except Exception as e:
        print(f"❌ Image URL test error: {e}")

def main():
    print("🚀 Complete Image Processing Workflow Test")
    print("=" * 60)
    
    # Test server status
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("❌ Server not running. Please start the server first.")
            return
    except:
        print("❌ Cannot connect to server. Please start the server first.")
        return
    
    # Run tests
    test_image_processing()
    
    print("\n✅ Complete workflow test finished!")

if __name__ == "__main__":
    main()
