import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_70B = os.getenv("GROQ_MODEL_70B", "llama-3.3-70b-versatile")
GROQ_MODEL_8B = os.getenv("GROQ_MODEL_8B", "llama-3.1-8b-instant")
DATABASE_URL = os.getenv("DATABASE_URL")
MAX_RESUME_MATCHES = int(os.getenv("MAX_RESUME_MATCHES", 10))
MATCH_SCORE_THRESHOLD = float(os.getenv("MATCH_SCORE_THRESHOLD", 0.78))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
