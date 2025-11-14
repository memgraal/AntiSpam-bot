import os
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "chat_users.db")

DB_URL = f"sqlite:///{DB_PATH}"

CAPTCHA_TIMEOUT = 30
BANNED_WORDS = ["реклама", "крипта", "бот", "подписывайся"]
