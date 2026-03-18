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
groups = db["groups"]

# 🔥 INDEXES (IMPORTANT FOR SPEED + NO DUPLICATES)
users.create_index("user_id", unique=True)
groups.create_index("chat_id", unique=True)

print("Database connected successfully 🚀")


# ================= DEFAULT USER =================

def default_user(user_id, name):
    now = int(time.time())

    return {
        "user_id": user_id,
        "name": name,

        # activity
        "messages": 0,
        "last_active": now,
        "last_seen": now,

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

    users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": default_user(user_id, name),  # 🔥 safe insert
            "$set": {
                "name": name,
                "last_active": now
            },
            "$inc": {
                "messages": 1
            }
        },
        upsert=True
    )


# ================= GROUP SYSTEM =================

def save_group(chat_id):
    try:
        groups.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
    except:
        pass  # duplicate safe


def get_groups():
    try:
        return [g["chat_id"] for g in groups.find()]
    except:
        return []


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


# ================= RESET USER =================

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