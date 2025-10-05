import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './SmartAssistant.css';

const SmartAssistant = () => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  // Voice recording functionality
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsListening(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Microphone access denied. Please allow microphone access to use voice features.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
  };

  // Process voice input through the complete pipeline
  const processVoiceInput = async (audioBlob) => {
    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'voice_input.wav');

      const response = await axios.post('http://localhost:8000/api/voice/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.status === 'success') {
        const { transcription, ai_response, audio } = response.data;
        
        // Add to conversation
        const newMessages = [
          ...conversation,
          { type: 'user', text: transcription, timestamp: new Date() },
          { type: 'assistant', text: ai_response, timestamp: new Date() }
        ];
        setConversation(newMessages);

        // Play the audio response
        if (audio) {
          const audioBlob = new Blob([Uint8Array.from(atob(audio), c => c.charCodeAt(0))], { type: 'audio/mp3' });
          const url = URL.createObjectURL(audioBlob);
          setAudioUrl(url);
          setIsSpeaking(true);
          
          if (audioRef.current) {
            audioRef.current.play();
          }
        }
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      console.error('Error processing voice input:', error);
      const errorMessage = { type: 'error', text: 'Sorry, I encountered an error processing your request.', timestamp: new Date() };
      setConversation([...conversation, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle text input
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim()) return;

    setIsProcessing(true);
    
    try {
      const response = await axios.post('http://localhost:8000/api/voice/chat', {
        text: currentMessage
      });

      if (response.data.status === 'success') {
        const newMessages = [
          ...conversation,
          { type: 'user', text: currentMessage, timestamp: new Date() },
          { type: 'assistant', text: response.data.response, timestamp: new Date() }
        ];
        setConversation(newMessages);
        setCurrentMessage('');
      }
    } catch (error) {
      console.error('Error processing text input:', error);
      const errorMessage = { type: 'error', text: 'Sorry, I encountered an error processing your request.', timestamp: new Date() };
      setConversation([...conversation, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle audio playback end
  const handleAudioEnd = () => {
    setIsSpeaking(false);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
  };

  // Clear conversation
  const clearConversation = () => {
    setConversation([]);
  };


  return (
    <div className="smart-assistant-container">
      <div className="assistant-header">
        <h2>Smart Assistant</h2>
        <p>Your AI-powered voice assistant for renewable energy insights</p>
      </div>

      {/* Voice Interface */}
      <div className="voice-interface">
        <div className="voice-controls">
          <div className="voice-button-container">
            <button
              className={`voice-button ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''} ${isSpeaking ? 'speaking' : ''}`}
              onClick={isListening ? stopRecording : startRecording}
              disabled={isProcessing}
            >
              <div className="voice-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
              </div>
              <div className="voice-ripple"></div>
            </button>
          </div>
          
          <div className="voice-status">
            {isListening && <span className="status-text listening">Listening...</span>}
            {isProcessing && <span className="status-text processing">Processing...</span>}
            {isSpeaking && <span className="status-text speaking">Speaking...</span>}
            {!isListening && !isProcessing && !isSpeaking && <span className="status-text idle">Click to speak</span>}
          </div>
        </div>

        {/* Text Input */}
        <form onSubmit={handleTextSubmit} className="text-input-form">
          <div className="input-group">
            <input
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Or type your message here..."
              className="text-input"
              disabled={isProcessing}
            />
            <button type="submit" className="send-button" disabled={isProcessing || !currentMessage.trim()}>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </form>
      </div>


      {/* Conversation Display */}
      <div className="conversation-container">
        <div className="conversation-header">
          <h3>Conversation</h3>
          <button onClick={clearConversation} className="clear-button">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
            Clear
          </button>
        </div>
        
        <div className="conversation-messages">
          {conversation.length === 0 ? (
            <div className="empty-conversation">
              <div className="empty-icon">💬</div>
              <p>Start a conversation with your smart assistant</p>
              <p className="empty-subtitle">Ask about renewable energy, sustainability, or any questions you have!</p>
            </div>
          ) : (
            conversation.map((message, index) => (
              <div key={index} className={`message ${message.type}`}>
                <div className="message-content">
                  <div className="message-text">{message.text}</div>
                  
                  
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Audio Element */}
      <audio
        ref={audioRef}
        onEnded={handleAudioEnd}
        style={{ display: 'none' }}
      >
        {audioUrl && <source src={audioUrl} type="audio/mp3" />}
      </audio>
    </div>
  );
};

export default SmartAssistant;
