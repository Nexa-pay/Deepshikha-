from pymongo import MongoClient
import os
import time

# ================= CONNECTION =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")

client = MongoClient(MONGO_URI)

db = client["telegram_bot"]

users = db["users"]
groups = db["groups"]

# ================= INDEXES =================

users.create_index("user_id", unique=True)
users.create_index("last_active")
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

        # personality
        "personality": {
            "type": "normal"
        },

        # interests
        "favorites": {
            "topics": []
        },

        # chat memory
        "history": [],

        # 🔥 future features
        "is_vip": False,
        "last_message": "",
    }


# ================= UPDATE USER =================

def update_user(user_id, name):
    now = int(time.time())

    try:
        users.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": default_user(user_id, name),
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
    except Exception as e:
        print("DB update error:", e)


# ================= GROUP SYSTEM =================

def save_group(chat_id):
    try:
        groups.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
    except Exception as e:
        print("Group save error:", e)


def get_groups():
    try:
        return [g["chat_id"] for g in groups.find({}, {"chat_id": 1})]
    except Exception as e:
        print("Group fetch error:", e)
        return []


# ================= USERS =================

def get_user(user_id):
    try:
        return users.find_one({"user_id": user_id})
    except Exception as e:
        print("Get user error:", e)
        return None


def reset_user(user_id):
    try:
        users.delete_one({"user_id": user_id})
    except Exception as e:
        print("Reset error:", e)


def clear_history(user_id):
    try:
        users.update_one(
            {"user_id": user_id},
            {"$set": {"history": []}}
        )
    except Exception as e:
        print("Clear history error:", e)


# ================= ANALYTICS =================

def get_top_users(limit=10):
    try:
        return list(
            users.find({}, {"name": 1, "messages": 1})
            .sort("messages", -1)
            .limit(limit)
        )
    except Exception as e:
        print("Top users error:", e)
        return []


def get_inactive_users(hours=6):
    now = int(time.time())
    gap = hours * 3600

    try:
        return list(
            users.find(
                {"last_active": {"$lt": now - gap}},
                {"name": 1}
            ).limit(10)
        )
    except Exception as e:
        print("Inactive users error:", e)
        return []