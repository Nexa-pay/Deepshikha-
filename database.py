import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]

print("Database connected successfully 🚀")


# ✅ Add or update user
def update_user(user_id, name):
    users.update_one(
        {"user_id": user_id},
        {
            "$set": {"name": name},
            "$inc": {"messages": 1}
        },
        upsert=True
    )


# ✅ Get top active users
def get_top_users(limit=5):
    return list(users.find().sort("messages", -1).limit(limit))


# ✅ Get inactive users
def get_inactive_users(limit=3):
    return list(users.find().sort("messages", 1).limit(limit))