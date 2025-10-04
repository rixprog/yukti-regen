import os
from groq import Groq
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


def transcribe_audio(audio_file_content: bytes, filename: str = "audio.wav"):
    """
    Transcribe audio file to text using Groq Whisper
    """
    transcription = groq_client.audio.transcriptions.create(
        file=(filename, audio_file_content),
        model="whisper-large-v3-turbo",
        response_format="json",
        language="en",
        temperature=0.0
    )
    return transcription.text


def get_ai_response(text: str):
    """
    Get AI response from Groq
    """
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful, friendly voice assistant. Keep responses conversational, natural, and concise. Speak like you're having a real conversation."
            },
            {"role": "user", "content": text}
        ],
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content


def text_to_speech_elevenlabs(text: str):
    """
    Convert text to speech using ElevenLabs and return audio bytes
    """
    audio_stream = elevenlabs_client.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_flash_v2_5",
        output_format="mp3_22050_32",
    )
    
    audio_chunks = []
    for chunk in audio_stream:
        if chunk:
            audio_chunks.append(chunk)
    
    return b''.join(audio_chunks)