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
