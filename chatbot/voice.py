import os
import wave
import pyaudio
import threading
from dotenv import load_dotenv
from groq import Groq
from elevenlabs.client import ElevenLabs
from elevenlabs import play

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

is_recording = False

def record_audio_until_enter():
    global is_recording
    
    print("🎤 Recording... Press ENTER to stop.")
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    frames = []
    is_recording = True
    
    def record():
        while is_recording:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
    
    record_thread = threading.Thread(target=record)
    record_thread.start()
    
    input()
    is_recording = False
    record_thread.join()
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return WAVE_OUTPUT_FILENAME

def transcribe_audio(filename):
    print("🎧 Transcribing...")
    with open(filename, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(filename, file.read()),
            model="whisper-large-v3-turbo",
            response_format="json",
            language="en",
            temperature=0.0
        )
    text = transcription.text
    print(f"📝 You said: {text}")
    return text

def get_ai_response(text):
    print("🤖 Getting AI response...")
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a helpful, friendly voice assistant. Keep responses conversational, natural, and concise. Speak like you're having a real conversation."},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
        max_tokens=1024
    )
    ai_text = response.choices[0].message.content
    print(f"💭 Assistant: {ai_text}")
    return ai_text

def text_to_speech_elevenlabs(text):
    print("🔊 Converting to speech...")
    audio_stream = elevenlabs_client.text_to_speech.stream(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",   
        model_id="eleven_flash_v2_5",        
        output_format="mp3_22050_32",     
    )
    
    audio_chunks = []
    for chunk in audio_stream:
        if chunk:
            audio_chunks.append(chunk)
    
    audio_data = b''.join(audio_chunks)
    print("🎵 Playing...")
    play.play(audio_data)

if __name__ == "__main__":
    audio_file = record_audio_until_enter()
    transcribed_text = transcribe_audio(audio_file)
    ai_response = get_ai_response(transcribed_text)
    text_to_speech_elevenlabs(ai_response)