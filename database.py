from pymongo import MongoClient
import os
import time

# ================= CONNECTION =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI missing")

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]

print("Database connected successfully 🚀")


# ================= DEFAULT USER =================

def default_user(user_id, name):
    return {
        "user_id": user_id,
        "name": name,

        # activity
        "messages": 0,
        "last_active": int(time.time()),
        "last_seen": int(time.time()),

        # emotional system
        "attachment": 0,
        "relationship": 0,
        "ignore_count": 0,

        # personality memory
        "personality": {
            "type": "normal"
        },

        "favorites": {
            "topics": []
        },

        # chat memory
        "history": []
    }


# ================= UPDATE USER =================

def update_user(user_id, name):
    now = int(time.time())

    existing = users.find_one({"user_id": user_id})

    if not existing:
        users.insert_one(default_user(user_id, name))
    else:
        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "last_active": now
                },
                "$inc": {
                    "messages": 1
                }
            }
        )


# ================= GET TOP USERS =================

def get_top_users(limit=10):
    return list(
        users.find().sort("messages", -1).limit(limit)
    )


# ================= GET INACTIVE USERS =================

def get_inactive_users(hours=6):
    now = int(time.time())
    gap = hours * 3600

    return list(
        users.find({
            "last_active": {"$lt": now - gap}
        }).limit(10)
    )


# ================= GET USER =================

def get_user(user_id):
    return users.find_one({"user_id": user_id})


# ================= RESET USER (OPTIONAL DEBUG) =================

def reset_user(user_id):
    users.delete_one({"user_id": user_id})


# ================= CLEAR HISTORY =================

def clear_history(user_id):
    users.update_one(
        {"user_id": user_id},
        {
            "$set": {"history": []}
        }
    )