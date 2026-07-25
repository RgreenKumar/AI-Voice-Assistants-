import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
    GOOGLE_TTS_API_KEY = os.getenv('GOOGLE_TTS_API_KEY', '')  # Optional: for voice synthesis
    MONGODB_URI = os.getenv('MONGODB_URI', '')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ai_voice_assistant')
    MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'conversations')

