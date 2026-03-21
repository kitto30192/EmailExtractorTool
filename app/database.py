from pymongo import MongoClient
import certifi
from app.config import MONGO_URI

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.email_extractor_db
users_collection = db.users

# --- NEW: Collection to track background jobs ---
jobs_collection = db.jobs