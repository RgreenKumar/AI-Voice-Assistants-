"""
Voice Service for Text-to-Speech and Speech-to-Text handling.
Uses Google Text-to-Speech API and Web Speech API (browser-side).
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class VoiceService:
    """Handle voice synthesis and audio playback."""
    
    def __init__(self):
        """Initialize voice service with API credentials if available."""
        self.google_tts_api_key = os.getenv('GOOGLE_TTS_API_KEY', '')
        self.use_google_tts = bool(self.google_tts_api_key)
        
    def text_to_speech(self, text: str, language_code: str = 'en-US') -> bytes | None:
        """
        Convert text to speech using Google Text-to-Speech API.
        Falls back to None if API key is not configured.
        
        Args:
            text: The text to convert to speech
            language_code: Language code (e.g., 'en-US', 'es-ES')
            
        Returns:
            Audio file bytes or None if API not configured
        """
        if not self.use_google_tts:
            return None
            
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.google_tts_api_key}"
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": language_code,
                    "name": f"{language_code}-Neural2-C"
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "pitch": 0,
                    "speakingRate": 1.0
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'audioContent' in data:
                import base64
                audio_bytes = base64.b64decode(data['audioContent'])
                return audio_bytes
                
        except Exception as e:
            print(f"Error in text_to_speech: {str(e)}")
            return None
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """
        Validate that audio data is in valid format.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if valid audio format
        """
        # Basic validation: check for WAV or MP3 headers
        return (
            len(audio_data) > 4 and
            (audio_data[:4] == b'RIFF' or audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb')
        )
    
    def process_voice_input(self, audio_file_path: str) -> str | None:
        """
        Process voice input file (speech-to-text).
        Note: This is typically handled by client-side Web Speech API,
        but this method can be used for additional processing.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None
        """
        # This could integrate with Google Cloud Speech-to-Text API
        # For now, speech-to-text is handled client-side
        return None
