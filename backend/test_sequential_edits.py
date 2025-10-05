#!/usr/bin/env python3
"""
Test script for sequential edit naming
"""

import os
import requests
from PIL import Image
import uuid
from datetime import datetime

def create_test_edit_images():
    """Create test edit images with sequential names"""
    os.makedirs("after_images", exist_ok=True)
    
    # Create test images: edit_1.jpg, edit_2.jpg, edit_3.jpg
    for i in range(1, 4):
        img = Image.new('RGB', (200, 200), color='blue')
        
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 100), f"EDIT {i}", fill='white', font=font)
        
        filename = f"edit_{i}.jpg"
        filepath = os.path.join("after_images", filename)
        img.save(filepath, 'JPEG', quality=95)
        
        print(f"✅ Created: {filepath}")

def test_edit_count():
    """Test edit count endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/images/edits/count")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Edit count: {data.get('edit_count', 0)}")
        else:
            print(f"❌ Edit count failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Edit count error: {e}")

def test_all_edits():
    """Test all edits endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/images/edits/all")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All edits: {data.get('count', 0)} images")
            for img in data.get('images', []):
                print(f"   - {img['filename']} (edit #{img.get('edit_number', 'N/A')})")
        else:
            print(f"❌ All edits failed: {response.status_code}")
    except Exception as e:
        print(f"❌ All edits error: {e}")

def test_image_urls():
    """Test if edit images can be accessed"""
    try:
        response = requests.get("http://localhost:8000/api/images/edits/all")
        if response.status_code == 200:
            data = response.json()
            for img in data.get('images', []):
                url = f"http://localhost:8000{img['url']}"
                print(f"Testing: {url}")
                
                img_response = requests.get(url)
                if img_response.status_code == 200:
                    print(f"✅ {img['filename']}: OK ({len(img_response.content)} bytes)")
                else:
                    print(f"❌ {img['filename']}: Failed ({img_response.status_code})")
    except Exception as e:
        print(f"❌ Image URL test error: {e}")

def main():
    print("🧪 Testing Sequential Edit Naming")
    print("=" * 50)
    
    # Create test images
    create_test_edit_images()
    
    # Test edit count
    test_edit_count()
    
    # Test all edits
    test_all_edits()
    
    # Test image URLs
    test_image_urls()
    
    print("\n✅ Sequential edit test complete!")

if __name__ == "__main__":
    main()
