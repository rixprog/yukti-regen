import os
import base64
from io import BytesIO
from PIL import Image
from google.genai import Client
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

# Initialize Gemini client
client = Client()

class ImageProcessor:
    def __init__(self):
        self.upload_dir = "uploaded_images"
        self.generated_dir = "generated_images"
        self.before_dir = "before_images"
        self.after_dir = "after_images"
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.generated_dir, exist_ok=True)
        os.makedirs(self.before_dir, exist_ok=True)
        os.makedirs(self.after_dir, exist_ok=True)
    
    def save_uploaded_image(self, image_file, filename: str = None) -> str:
        """Save uploaded image and return the file path"""
        if not filename:
            filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        file_path = os.path.join(self.upload_dir, filename)
        
        # Open and save the image
        image = Image.open(image_file)
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(file_path, 'JPEG', quality=95)
        
        return file_path
    
    def get_next_edit_number(self) -> int:
        """Get the next sequential edit number"""
        if not os.path.exists(self.after_dir):
            return 1
        
        # Get all files in after directory
        files = [f for f in os.listdir(self.after_dir) if f.startswith('edit_') and f.endswith('.jpg')]
        
        if not files:
            return 1
        
        # Extract numbers from filenames
        numbers = []
        for file in files:
            try:
                # Extract number from "edit_X.jpg"
                num_str = file.replace('edit_', '').replace('.jpg', '')
                numbers.append(int(num_str))
            except ValueError:
                continue
        
        if not numbers:
            return 1
        
        return max(numbers) + 1

    def process_image_with_ai(self, image_path: str, prompt: str) -> dict:
        """Process image with AI using Gemini API"""
        try:
            # Load the image
            image = Image.open(image_path)
            
            # Save original to before folder
            before_filename = f"before_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            before_path = os.path.join(self.before_dir, before_filename)
            image.save(before_path, 'JPEG', quality=95)
            
            # Call Gemini model with prompt + image
            print("⏳ Generating edited image(s) with Gemini...")
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt, image],
            )
            
            # Get starting edit number
            start_edit_num = self.get_next_edit_number()
            
            # Extract and save generated images with sequential names
            generated_images = []
            for idx, part in enumerate(response.candidates[0].content.parts, start=1):
                if part.inline_data is not None:
                    img = Image.open(BytesIO(part.inline_data.data))
                    
                    # Create sequential filename: edit_1.jpg, edit_2.jpg, etc.
                    edit_num = start_edit_num + idx - 1
                    after_filename = f"edit_{edit_num}.jpg"
                    after_path = os.path.join(self.after_dir, after_filename)
                    img.save(after_path, 'JPEG', quality=95)
                    
                    generated_images.append({
                        "filename": after_filename,
                        "path": after_path,
                        "url": f"/api/images/after/{after_filename}",
                        "edit_number": edit_num
                    })
            
            return {
                "status": "success",
                "original_image": {
                    "filename": os.path.basename(image_path),
                    "path": image_path,
                    "url": f"/api/images/uploaded/{os.path.basename(image_path)}"
                },
                "before_image": {
                    "filename": before_filename,
                    "path": before_path,
                    "url": f"/api/images/before/{before_filename}"
                },
                "generated_images": generated_images,
                "prompt": prompt,
                "count": len(generated_images),
                "edit_numbers": [img["edit_number"] for img in generated_images]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI image processing failed: {str(e)}"
            }
    
    def generate_image_from_prompt(self, prompt: str) -> dict:
        """Generate image from text prompt using Gemini API"""
        try:
            print("⏳ Generating image from prompt with Gemini...")
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt],
            )
            
            # Extract and save generated images
            generated_images = []
            for idx, part in enumerate(response.candidates[0].content.parts, start=1):
                if part.inline_data is not None:
                    img = Image.open(BytesIO(part.inline_data.data))
                    filename = f"generated_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg"
                    file_path = os.path.join(self.generated_dir, filename)
                    img.save(file_path, 'JPEG', quality=95)
                    
                    generated_images.append({
                        "filename": filename,
                        "path": file_path,
                        "url": f"/api/images/generated/{filename}"
                    })
            
            return {
                "status": "success",
                "generated_images": generated_images,
                "prompt": prompt,
                "count": len(generated_images)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI image generation failed: {str(e)}"
            }
    
    def get_image_url(self, image_type: str, filename: str) -> str:
        """Get URL for serving images"""
        if image_type == "uploaded":
            return f"/api/images/uploaded/{filename}"
        elif image_type == "generated":
            return f"/api/images/generated/{filename}"
        elif image_type == "before":
            return f"/api/images/before/{filename}"
        elif image_type == "after":
            return f"/api/images/after/{filename}"
        else:
            return None
    
    def get_edit_count(self) -> int:
        """Get the total count of edit images"""
        if not os.path.exists(self.after_dir):
            return 0
        
        files = [f for f in os.listdir(self.after_dir) if f.startswith('edit_') and f.endswith('.jpg')]
        return len(files)

    def list_images(self, image_type: str) -> list:
        """List all images of a specific type"""
        if image_type == "uploaded":
            dir_path = self.upload_dir
        elif image_type == "generated":
            dir_path = self.generated_dir
        elif image_type == "before":
            dir_path = self.before_dir
        elif image_type == "after":
            dir_path = self.after_dir
        else:
            return []
        
        images = []
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    file_path = os.path.join(dir_path, filename)
                    stat = os.stat(file_path)
                    
                    # Extract edit number for after images
                    edit_number = None
                    if image_type == "after" and filename.startswith('edit_'):
                        try:
                            edit_number = int(filename.replace('edit_', '').replace('.jpg', ''))
                        except ValueError:
                            pass
                    
                    images.append({
                        "filename": filename,
                        "path": file_path,
                        "url": self.get_image_url(image_type, filename),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "edit_number": edit_number
                    })
        
        # Sort by edit number for after images, by creation time for others
        if image_type == "after":
            return sorted(images, key=lambda x: x['edit_number'] or 0)
        else:
            return sorted(images, key=lambda x: x['created'], reverse=True)
