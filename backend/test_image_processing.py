#!/usr/bin/env python3
"""
Test script for image processing functionality
"""

import os
import sys
import requests
from PIL import Image
import io

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_image.jpg"

def create_test_image():
    """Create a simple test image"""
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color='red')
    
    # Add some text or pattern
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 100), "TEST IMAGE", fill='white', font=font)
    
    # Save the test image
    img.save(TEST_IMAGE_PATH, 'JPEG')
    print(f"✅ Created test image: {TEST_IMAGE_PATH}")

def test_image_upload():
    """Test image upload endpoint"""
    print("\n🧪 Testing image upload...")
    
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'image_file': f}
            response = requests.post(f"{BASE_URL}/api/images/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Image upload successful")
                print(f"   Filename: {data.get('filename')}")
                print(f"   URL: {data.get('url')}")
                return data.get('url')
            else:
                print(f"❌ Upload failed: {data.get('message')}")
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    return None

def test_image_generation():
    """Test image generation from prompt"""
    print("\n🧪 Testing image generation...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/images/generate", json={
            "prompt": "A beautiful sunset over mountains with renewable energy wind turbines"
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Image generation successful")
                print(f"   Generated {data.get('count')} image(s)")
                for i, img in enumerate(data.get('generated_images', [])):
                    print(f"   Image {i+1}: {img.get('filename')}")
                return True
            else:
                print(f"❌ Generation failed: {data.get('message')}")
        else:
            print(f"❌ Generation failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Generation error: {e}")
    
    return False

def test_image_processing():
    """Test image processing with AI"""
    print("\n🧪 Testing image processing...")
    
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'image_file': f}
            data = {'prompt': 'Make this image more colorful and add some artistic effects'}
            response = requests.post(f"{BASE_URL}/api/images/process", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ Image processing successful")
                print(f"   Generated {result.get('count')} image(s)")
                for i, img in enumerate(result.get('generated_images', [])):
                    print(f"   Processed Image {i+1}: {img.get('filename')}")
                return True
            else:
                print(f"❌ Processing failed: {result.get('message')}")
        else:
            print(f"❌ Processing failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Processing error: {e}")
    
    return False

def test_image_listing():
    """Test image listing endpoints"""
    print("\n🧪 Testing image listing...")
    
    image_types = ['uploaded', 'generated', 'before', 'after']
    
    for img_type in image_types:
        try:
            response = requests.get(f"{BASE_URL}/api/images/list/{img_type}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    count = data.get('count', 0)
                    print(f"✅ {img_type.capitalize()} images: {count}")
                else:
                    print(f"❌ Failed to list {img_type} images: {data.get('message')}")
            else:
                print(f"❌ Failed to list {img_type} images with status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error listing {img_type} images: {e}")

def cleanup():
    """Clean up test files"""
    if os.path.exists(TEST_IMAGE_PATH):
        os.remove(TEST_IMAGE_PATH)
        print(f"\n🧹 Cleaned up test image: {TEST_IMAGE_PATH}")

def main():
    """Run all tests"""
    print("🚀 Starting Image Processing Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server not running. Please start the backend server first.")
            return
    except:
        print("❌ Cannot connect to server. Please start the backend server first.")
        return
    
    # Create test image
    create_test_image()
    
    # Run tests
    test_image_upload()
    test_image_generation()
    test_image_processing()
    test_image_listing()
    
    # Cleanup
    cleanup()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
