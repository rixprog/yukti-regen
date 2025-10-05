#!/usr/bin/env python3
"""
Test static file serving for images
"""

import os
import requests
from PIL import Image
import uuid
from datetime import datetime

def create_test_image_in_after_folder():
    """Create a test image in the after_images folder"""
    # Create after_images directory if it doesn't exist
    os.makedirs("after_images", exist_ok=True)
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color='blue')
    
    # Add some text
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 100), "TEST AFTER", fill='white', font=font)
    
    # Generate filename
    filename = f"test_after_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join("after_images", filename)
    
    # Save the image
    img.save(filepath, 'JPEG', quality=95)
    
    print(f"✅ Created test image: {filepath}")
    return filename

def test_static_file_serving():
    """Test if static files are being served correctly"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Static File Serving")
    print("=" * 50)
    
    # Create test image
    filename = create_test_image_in_after_folder()
    
    # Test the static file endpoint
    test_url = f"{base_url}/api/images/after/{filename}"
    print(f"\nTesting URL: {test_url}")
    
    try:
        response = requests.get(test_url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Static file serving works!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {len(response.content)} bytes")
        else:
            print(f"❌ Static file serving failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing static files: {e}")

def check_directory_structure():
    """Check if directories exist and list files"""
    print("\n📁 Checking Directory Structure")
    print("=" * 50)
    
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            print(f"✅ {dir_name}: {len(files)} files")
            if files:
                print(f"   Files: {files[:3]}{'...' if len(files) > 3 else ''}")
        else:
            print(f"❌ {dir_name}: Directory does not exist")

if __name__ == "__main__":
    check_directory_structure()
    test_static_file_serving()
