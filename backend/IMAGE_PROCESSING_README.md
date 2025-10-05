# AI Image Processing Features

This document describes the AI image processing features added to the Smart Assistant.

## Features

### 1. Image Upload
- Upload images through the frontend interface
- Images are saved in the `uploaded_images` directory
- Support for common image formats (JPEG, PNG, GIF)

### 2. AI Image Generation
- Generate images from text prompts using Gemini API
- Generated images are saved in the `generated_images` directory
- Multiple images can be generated from a single prompt

### 3. AI Image Processing/Editing
- Upload an image and provide editing instructions
- AI processes the image based on the prompt
- Original images are saved in `before_images` directory
- Processed images are saved in `after_images` directory

### 4. Image Management
- List images by type (uploaded, generated, before, after)
- Serve images through static file endpoints
- Automatic cleanup and organization

## API Endpoints

### Image Upload
```
POST /api/images/upload
- Content-Type: multipart/form-data
- Body: image_file (file)
- Response: {status, message, filename, url}
```

### Image Processing
```
POST /api/images/process
- Content-Type: multipart/form-data
- Body: image_file (file), prompt (string)
- Response: {status, original_image, before_image, generated_images, count}
```

### Image Generation
```
POST /api/images/generate
- Content-Type: application/json
- Body: {prompt: string}
- Response: {status, generated_images, count}
```

### List Images
```
GET /api/images/list/{image_type}
- image_type: uploaded, generated, before, after
- Response: {status, images, count}
```

## Directory Structure

```
backend/
├── uploaded_images/     # User uploaded images
├── generated_images/    # AI generated images
├── before_images/       # Original images before processing
├── after_images/        # Processed images
└── image_processor.py   # Image processing logic
```

## Frontend Integration

### Toggle Feature
- Users can enable/disable AI image features with a toggle switch
- When disabled, only normal voice/text chat is available
- When enabled, image processing interface appears

### Image Interface
- Drag & drop or click to upload images
- Preview uploaded images
- Enter prompts for generation or editing
- View generated/processed images in conversation
- Clear all image data

### Conversation Integration
- Images are displayed in conversation history
- Generated images show in assistant responses
- Original images show in user messages

## Dependencies

### Backend
- `PIL` (Pillow) - Image processing
- `google.genai` - Gemini API client
- `fastapi` - Web framework
- `python-multipart` - File upload support
- `aiofiles` - Async file operations

### Frontend
- React hooks for state management
- Axios for API calls
- File input handling
- Image preview and display

## Usage Examples

### 1. Generate Image from Prompt
```javascript
// Frontend
const response = await axios.post('/api/images/generate', {
  prompt: "A solar farm in a green landscape"
});
```

### 2. Process Uploaded Image
```javascript
// Frontend
const formData = new FormData();
formData.append('image_file', selectedFile);
formData.append('prompt', 'Make this image more vibrant');

const response = await axios.post('/api/images/process', formData);
```

### 3. List Generated Images
```javascript
// Frontend
const response = await axios.get('/api/images/list/generated');
const images = response.data.images;
```

## Error Handling

- File type validation (images only)
- API error responses with descriptive messages
- Image loading fallbacks with placeholder
- Network error handling with user feedback

## Security Considerations

- File type validation on upload
- File size limits (configurable)
- Secure file storage in designated directories
- CORS configuration for frontend access

## Testing

Run the test script to verify functionality:
```bash
cd backend
python test_image_processing.py
```

## Configuration

### Environment Variables
- `GEMINI_API_KEY` - Required for AI image processing
- Image storage paths are configurable in `ImageProcessor` class

### API Configuration
- CORS settings for frontend access
- Static file serving for images
- File upload size limits

## Future Enhancements

- Batch image processing
- Image format conversion
- Advanced image filters
- Image metadata extraction
- Cloud storage integration
- Image compression optimization
