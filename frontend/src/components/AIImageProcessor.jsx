import React, { useState, useRef } from 'react';
import axios from 'axios';
import './AIImageProcessor.css';

const AIImageProcessor = () => {
  // Image processing states
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImages, setGeneratedImages] = useState([]);
  const [isImageProcessing, setIsImageProcessing] = useState(false);
  
  const fileInputRef = useRef(null);

  // Image processing functions
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const processImageWithAI = async () => {
    if (!selectedImage || !imagePrompt.trim()) {
      alert('Please select an image and enter a prompt');
      return;
    }

    console.log('Processing image with AI:', { 
      imageName: selectedImage.name, 
      prompt: imagePrompt 
    });

    setIsImageProcessing(true);
    try {
      const formData = new FormData();
      formData.append('image_file', selectedImage);
      formData.append('prompt', imagePrompt);

      console.log('Sending request to /api/images/process');

      const response = await axios.post('http://localhost:8000/api/images/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Response received:', response.data);

      if (response.data.status === 'success') {
        console.log('Generated images URLs:', response.data.generated_images.map(img => img.url));
        setGeneratedImages(response.data.generated_images);
        
        // Clear form
        setImagePrompt('');
        setSelectedImage(null);
        setImagePreview(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('Error processing image:', error);
      alert('Failed to process image: ' + error.message);
    } finally {
      setIsImageProcessing(false);
    }
  };

  const generateImageFromPrompt = async () => {
    if (!imagePrompt.trim()) {
      alert('Please enter a prompt');
      return;
    }

    console.log('Generating image from prompt:', imagePrompt);

    setIsImageProcessing(true);
    try {
      console.log('Sending request to /api/images/generate');

      const response = await axios.post('http://localhost:8000/api/images/generate', {
        prompt: imagePrompt
      });

      console.log('Response received:', response.data);

      if (response.data.status === 'success') {
        console.log('Generated images URLs:', response.data.generated_images.map(img => img.url));
        setGeneratedImages(response.data.generated_images);
        
        // Clear form
        setImagePrompt('');
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('Error generating image:', error);
      alert('Failed to generate image: ' + error.message);
    } finally {
      setIsImageProcessing(false);
    }
  };

  const clearImageData = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setImagePrompt('');
    setGeneratedImages([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="ai-image-processor">
      <div className="processor-header">
        <h2>AI Image Processor</h2>
        <p>Generate and edit images using AI technology</p>
      </div>

      <div className="image-processing-interface">
        <div className="image-section">
          <h3>AI Image Processing</h3>
          
          {/* Image Upload */}
          <div className="image-upload-section">
            <div className="upload-area">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
              />
              <button
                className="upload-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isImageProcessing}
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                </svg>
                Upload Image
              </button>
              {selectedImage && (
                <span className="selected-file">
                  {selectedImage.name}
                </span>
              )}
            </div>
            
            {imagePreview && (
              <div className="image-preview">
                <img src={imagePreview} alt="Preview" />
              </div>
            )}
          </div>

          {/* Prompt Input */}
          <div className="prompt-section">
            <form onSubmit={(e) => {
              e.preventDefault();
              if (selectedImage) {
                processImageWithAI();
              } else {
                generateImageFromPrompt();
              }
            }} className="prompt-form">
              <div className="input-group">
                <input
                  type="text"
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  placeholder="Enter your image prompt or editing instruction..."
                  className="prompt-input"
                  disabled={isImageProcessing}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (selectedImage) {
                        processImageWithAI();
                      } else {
                        generateImageFromPrompt();
                      }
                    }
                  }}
                />
                <div className="prompt-buttons">
                  {selectedImage ? (
                    <button
                      type="submit"
                      className="process-button"
                      disabled={isImageProcessing || !imagePrompt.trim()}
                    >
                      {isImageProcessing ? (
                        <>
                          <svg className="loading-spinner" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z" />
                          </svg>
                          Processing...
                        </>
                      ) : (
                        'Process Image'
                      )}
                    </button>
                  ) : (
                    <button
                      type="submit"
                      className="generate-button"
                      disabled={isImageProcessing || !imagePrompt.trim()}
                    >
                      {isImageProcessing ? (
                        <>
                          <svg className="loading-spinner" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z" />
                          </svg>
                          Generating...
                        </>
                      ) : (
                        'Generate Image'
                      )}
                    </button>
                  )}
                  <button
                    type="button"
                    className="clear-button"
                    onClick={clearImageData}
                    disabled={isImageProcessing}
                  >
                    Clear
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Processing Status */}
          {isImageProcessing && (
            <div className="processing-status">
              <div className="status-message">
                <svg className="loading-spinner" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z" />
                </svg>
                <span>
                  {selectedImage ? 'Processing your image with AI...' : 'Generating image from your prompt...'}
                </span>
              </div>
            </div>
          )}

          {/* Generated Images Display */}
          {generatedImages.length > 0 && (
            <div className="generated-images">
              <h4>Generated Images</h4>
              <div className="image-grid">
                {generatedImages.map((img, index) => (
                  <div key={index} className="generated-image-item">
                    <img 
                      src={`http://localhost:8000${img.url}`} 
                      alt={`Generated ${index + 1}`}
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
                      }}
                    />
                    <div className="image-info">
                      <span className="image-filename">{img.filename}</span>
                      {img.edit_number && (
                        <span className="edit-number">Edit #{img.edit_number}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIImageProcessor;
