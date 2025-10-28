"""
Speech Integration Module for EVA

This module connects the speech processing capabilities with the rest of the EVA system,
including message handling, response generation, and memory management.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
import sys

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# from speech.speech_processor import SpeechProcessor
from utils.response_generator import generate_response
# from nlp.sentiment_analysis import analyze_sentiment_and_emotion
from memory.conversation_memory import ConversationMemory

class SpeechIntegration:
    """
    Integrates speech processing with EVA's core capabilities
    """
    
    def __init__(self, user_id=None):
        """
        Initialize speech integration
        
        Args:
            user_id (str): User ID for personalization
        """
        # self.speech_processor = SpeechProcessor(
        #     whisper_model=os.environ.get('WHISPER_MODEL', 'base'),
        #     elevenlabs_api_key=os.environ.get('ELEVENLABS_API_KEY')
        # )
        
        self.user_id = user_id
        self.conversation_memory = None
        
        # Initialize conversation memory if user_id is provided
        if user_id:
            self.conversation_memory = ConversationMemory(user_id=user_id)
    
    def process_audio_message(self, audio_base64, audio_format="wav", language=None, 
                              user_preference=None, chat_id=None, tts_enabled=True,
                              voice_id="21m00Tcm4TlvDq8ikWAM"):
        """
        Process an audio message and generate a response
        
        Args:
            audio_base64 (str): Base64-encoded audio data
            audio_format (str): Audio format (wav, mp3, etc.)
            language (str): Language code (optional)
            user_preference (object): User preference object
            chat_id (str): Chat ID for conversation context
            tts_enabled (bool): Whether to enable text-to-speech for the response
            voice_id (str): ElevenLabs voice ID for response
            
        Returns:
            dict: Processing results including transcription and response
        """
        print("Speech processing is disabled.")
        return {"error": "Speech processing is disabled."}
    
    def get_available_voices(self):
        """
        Get available voices from ElevenLabs
        
        Returns:
            dict: Available voices
        """
        print("Speech processing is disabled.")
        return {"error": "Speech processing is disabled."}
    
    def text_to_speech(self, text, voice_id="21m00Tcm4TlvDq8ikWAM"):
        """
        Convert text to speech
        
        Args:
            text (str): Text to convert to speech
            voice_id (str): ElevenLabs voice ID
            
        Returns:
            dict: Speech synthesis results
        """
        print("Speech processing is disabled.")
        return {"error": "Speech processing is disabled."}