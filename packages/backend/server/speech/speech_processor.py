import os
import tempfile
import numpy as np
# Whisper is optional and may fail to import on some systems (no GPU or missing libs).
try:
    import whisper
except Exception:
    whisper = None
# from pydub import AudioSegment
import io
import base64
import requests
import json
from datetime import datetime
import time

class SpeechProcessor:
    """Class for speech processing using Whisper and ElevenLabs"""
    
    def __init__(self, whisper_model="base", elevenlabs_api_key=None):
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self.elevenlabs_api_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.processing_history = []
    
    def load_whisper_model(self):
        """Load the Whisper model"""
        if self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                print(f"Whisper model '{self.whisper_model_name}' loaded successfully.")
                return True
            except Exception as e:
                print(f"Error loading Whisper model: {str(e)}")
                return False
        return True
    
    def transcribe_audio(self, audio_file=None, audio_data=None, language=None):
        """
        Transcribe audio using Whisper
        
        Args:
            audio_file (str): Path to audio file
            audio_data (bytes): Raw audio data
            language (str): Language code (optional)
            
        Returns:
            dict: Transcription results
        """
        print("Audio transcription is disabled.")
        return {"error": "Audio transcription is disabled."}
    
    def transcribe_audio_base64(self, base64_audio, audio_format="wav", language=None):
        """
        Transcribe audio from base64 string
        
        Args:
            base64_audio (str): Base64-encoded audio data
            audio_format (str): Audio format (wav, mp3, etc.)
            language (str): Language code (optional)
            
        Returns:
            dict: Transcription results
        """
        if not self.load_whisper_model():
            return {"error": "Whisper model not loaded."}

        try:
            audio_bytes = base64.b64decode(base64_audio)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp_audio_file:
                tmp_audio_file.write(audio_bytes)
                tmp_audio_path = tmp_audio_file.name

            model_result = self.whisper_model.transcribe(tmp_audio_path, language=language)
            transcription = model_result["text"]

            os.remove(tmp_audio_path) # Clean up temp file

            # Placeholder for keyword/phrase recognition
            recognized_command = self._recognize_voice_command(transcription)

            self.processing_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "transcription",
                "audio_format": audio_format,
                "language": language,
                "transcription": transcription,
                "recognized_command": recognized_command
            })

            return {"transcription": transcription, "recognized_command": recognized_command}
        except Exception as e:
            print(f"Error transcribing audio from base64: {str(e)}")
            return {"error": str(e)}

    def _recognize_voice_command(self, text: str) -> str | None:
        """
        Recognize specific voice commands from the transcribed text.
        This is a simple keyword-based recognition. For more robustness,
        this would integrate with intent recognition.
        """
        text_lower = text.lower()
        if "summarize this" in text_lower:
            return "summarize_document"
        elif "set a reminder" in text_lower:
            return "set_reminder"
        elif "create a task" in text_lower:
            return "create_task"
        elif "show my schedule" in text_lower:
            return "show_schedule"
        return None
    
    def text_to_speech(self, text, voice_id="21m00Tcm4TlvDq8ikWAM", model_id="eleven_monolingual_v1"):
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text (str): Text to convert to speech
            voice_id (str): ElevenLabs voice ID
            model_id (str): ElevenLabs model ID
            
        Returns:
            dict: Speech synthesis results
        """
        print("Text-to-speech is disabled.")
        return {"error": "Text-to-speech is disabled."}
    
    def get_available_voices(self):
        """
        Get available voices from ElevenLabs
        
        Returns:
            dict: Available voices
        """
        print("Getting available voices is disabled.")
        return {"error": "Getting available voices is disabled."}
    
    def process_conversation(self, audio_file=None, audio_data=None, audio_base64=None, audio_format="wav", language=None):
        """
        Process a conversation: transcribe audio and generate a response
        
        Args:
            audio_file (str): Path to audio file
            audio_data (bytes): Raw audio data
            audio_base64 (str): Base64-encoded audio data
            audio_format (str): Audio format (wav, mp3, etc.)
            language (str): Language code (optional)
            
        Returns:
            dict: Conversation processing results
        """
        print("Conversation processing is disabled.")
        return {"error": "Conversation processing is disabled."}
    
    def get_processing_history(self):
        """
        Get processing history
        """
        return self.processing_history