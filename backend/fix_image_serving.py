#!/usr/bin/env python3
"""
Script to fix image serving issues
"""

import os
import shutil
from pathlib import Path

def ensure_directories_exist():
    """Ensure all image directories exist"""
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    print("📁 Ensuring directories exist...")
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ {dir_name}")
    
    return True

def check_permissions():
    """Check directory permissions"""
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    print("\n🔐 Checking permissions...")
    for dir_name in directories:
        if os.path.exists(dir_name):
            stat = os.stat(dir_name)
            print(f"✅ {dir_name}: {oct(stat.st_mode)[-3:]}")
        else:
            print(f"❌ {dir_name}: Does not exist")

def create_test_files():
    """Create test files in each directory"""
    from PIL import Image
    import uuid
    from datetime import datetime
    
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    colors = ["red", "green", "blue", "yellow"]
    
    print("\n🖼️ Creating test files...")
    for i, dir_name in enumerate(directories):
        if os.path.exists(dir_name):
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color=colors[i])
            
            filename = f"test_{dir_name}_{uuid.uuid4()}.jpg"
            filepath = os.path.join(dir_name, filename)
            
            img.save(filepath, 'JPEG')
            print(f"✅ Created: {filepath}")

def list_files():
    """List files in each directory"""
    directories = ["uploaded_images", "generated_images", "before_images", "after_images"]
    
    print("\n📋 Directory contents:")
    for dir_name in directories:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            print(f"📁 {dir_name}: {len(files)} files")
            if files:
                for file in files[:3]:  # Show first 3 files
                    filepath = os.path.join(dir_name, file)
                    size = os.path.getsize(filepath)
                    print(f"   - {file} ({size} bytes)")
        else:
            print(f"❌ {dir_name}: Does not exist")

def main():
    print("🔧 Fixing Image Serving Issues")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories_exist()
    
    # Check permissions
    check_permissions()
    
    # Create test files
    create_test_files()
    
    # List files
    list_files()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Start the server: python main.py")
    print("2. Open test_image_urls.html in your browser")
    print("3. Run debug_images.py to test the endpoints")

if __name__ == "__main__":
    main()
