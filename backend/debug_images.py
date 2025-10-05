#!/usr/bin/env python3
"""
Debug script to check image serving issues
"""

import os
import requests
import json
from PIL import Image
import uuid
from datetime import datetime

def create_test_images():
    """Create test images in all directories"""
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        
        # Create a test image
        img = Image.new('RGB', (200, 200), color='red' if 'after' in dir_name else 'blue')
        
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 100), f"TEST {dir_name.upper()}", fill='white', font=font)
        
        # Generate filename
        filename = f"test_{dir_name}_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(dir_name, filename)
        
        # Save the image
        img.save(filepath, 'JPEG', quality=95)
        
        print(f"✅ Created test image: {filepath}")
        return filename

def test_server_status():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ Server is running: {response.status_code}")
        return True
    except:
        print("❌ Server is not running")
        return False

def test_image_directories():
    """Test image directories"""
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    print("\n📁 Checking directories:")
    for dir_name in directories:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            print(f"✅ {dir_name}: {len(files)} files")
            if files:
                print(f"   Latest file: {files[-1]}")
        else:
            print(f"❌ {dir_name}: Directory does not exist")

def test_api_endpoints():
    """Test API endpoints"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing API endpoints:")
    
    # Test image test endpoint
    try:
        response = requests.get(f"{base_url}/api/images/test")
        if response.status_code == 200:
            data = response.json()
            print("✅ Image test endpoint works")
            print(f"   Directories: {json.dumps(data.get('directories', {}), indent=2)}")
        else:
            print(f"❌ Image test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Image test endpoint error: {e}")
    
    # Test list after images
    try:
        response = requests.get(f"{base_url}/api/images/list/after")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ After images list: {data.get('count', 0)} images")
            if data.get('images'):
                for img in data['images'][:3]:  # Show first 3
                    print(f"   - {img['filename']}: {img['url']}")
        else:
            print(f"❌ After images list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ After images list error: {e}")

def test_static_file_access():
    """Test direct static file access"""
    base_url = "http://localhost:8000"
    
    print("\n🔗 Testing static file access:")
    
    # Get list of after images first
    try:
        response = requests.get(f"{base_url}/api/images/list/after")
        if response.status_code == 200:
            data = response.json()
            if data.get('images'):
                test_image = data['images'][0]  # Get first image
                test_url = f"{base_url}{test_image['url']}"
                print(f"Testing URL: {test_url}")
                
                # Try to access the image
                img_response = requests.get(test_url)
                print(f"Image access status: {img_response.status_code}")
                
                if img_response.status_code == 200:
                    print("✅ Static file serving works!")
                    print(f"   Content-Type: {img_response.headers.get('content-type')}")
                    print(f"   Content-Length: {len(img_response.content)} bytes")
                else:
                    print(f"❌ Static file serving failed: {img_response.text}")
            else:
                print("❌ No images found to test")
        else:
            print("❌ Could not get image list")
    except Exception as e:
        print(f"❌ Static file test error: {e}")

def main():
    print("🔍 Debugging Image Serving Issues")
    print("=" * 50)
    
    # Test server
    if not test_server_status():
        print("Please start the server first: python main.py")
        return
    
    # Create test images
    create_test_images()
    
    # Test directories
    test_image_directories()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test static file access
    test_static_file_access()
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    main()
