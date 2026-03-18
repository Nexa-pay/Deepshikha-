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

# 🔥 INDEXES (NO DUPLICATE)
users.create_index("user_id", unique=True)
groups.create_index("chat_id", unique=True)

print("Database connected successfully 🚀")


# ================= UPDATE USER (FINAL FIX) =================

def update_user(user_id, name):
    now = int(time.time())

    try:
        users.update_one(
            {"user_id": user_id},
            {
                # 🔥 only insert fields here (NO name)
                "$setOnInsert": {
                    "user_id": user_id,
                    "messages": 0,
                    "last_active": now,
                    "last_seen": now,
                    "attachment": 0,
                    "relationship": 0,
                    "ignore_count": 0,
                    "personality": {"type": "normal"},
                    "favorites": {"topics": []},
                    "history": []
                },

                # 🔥 update always
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
        return [g["chat_id"] for g in groups.find()]
    except Exception as e:
        print("Group fetch error:", e)
        return []


# ================= GET TOP USERS =================

def get_top_users(limit=10):
    try:
        return list(
            users.find().sort("messages", -1).limit(limit)
        )
    except Exception as e:
        print("Top users error:", e)
        return []


# ================= GET INACTIVE USERS =================

def get_inactive_users(hours=6):
    now = int(time.time())
    gap = hours * 3600

    try:
        return list(
            users.find({
                "last_active": {"$lt": now - gap}
            }).limit(10)
        )
    except Exception as e:
        print("Inactive users error:", e)
        return []


# ================= GET USER =================

def get_user(user_id):
    try:
        return users.find_one({"user_id": user_id})
    except Exception as e:
        print("Get user error:", e)
        return None


# ================= RESET USER =================

def reset_user(user_id):
    try:
        users.delete_one({"user_id": user_id})
    except Exception as e:
        print("Reset error:", e)


# ================= CLEAR HISTORY =================

def clear_history(user_id):
    try:
        users.update_one(
            {"user_id": user_id},
            {"$set": {"history": []}}
        )
    except Exception as e:
        print("Clear history error:", e)