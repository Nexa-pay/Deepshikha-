from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["telegram_ai"]

users = db["users"]

print("✅ Database connected successfully 🚀")


# ================= USER SAVE =================

def update_user(user_id, name):
    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "name": name
            }
        },
        upsert=True
    )


# ================= SAVE MESSAGE =================

def save_message(user_id, text, reply):
    users.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "history": {
                    "$each": [
                        {"role": "user", "text": text},
                        {"role": "bot", "text": reply}
                    ],
                    "$slice": -20
                }
            }
        },
        upsert=True
    )


# ================= GET HISTORY =================

def get_history(user_id):
    data = users.find_one({"user_id": user_id}) or {}
    return data.get("history", [])