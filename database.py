from pymongo import MongoClient
import os

# ---------------- MONGODB CONNECTION ----------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)

db = client["telegram_bot"]

# ---------------- COLLECTIONS ----------------

users = db["users"]        # store users
groups = db["groups"]      # store group chats
tokens = db["tokens"]      # for paid system (future ready)

# ---------------- INDEXES (PERFORMANCE BOOST) ----------------

users.create_index("user_id", unique=True)
groups.create_index("chat_id", unique=True)
tokens.create_index("user_id")

print("Database connected successfully 🚀")