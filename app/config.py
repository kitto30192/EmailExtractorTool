import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable!")

SECRET_KEY = os.getenv("SECRET_KEY", "your_fallback_secret_key")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")