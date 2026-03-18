import os
import time
from pymongo import MongoClient

# ================= CONNECTION =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]
groups = db["groups"]

# 🔥 INDEXES (FAST + SAFE)
users.create_index("user_id", unique=True)
users.create_index("last_active")
users.create_index("messages")  # 🔥 leaderboard fast
groups.create_index("chat_id", unique=True)

print("Database connected successfully 🚀")


# ================= UPDATE USER =================

def update_user(user_id, name):
    now = int(time.time())

    try:
        users.update_one(
            {"user_id": user_id},
            {
                # 🔥 first time insert only
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

                # 🔥 always update (SAFE NAME FIX)
                "$set": {
                    "name": name if name else "user",
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
        return [g["chat_id"] for g in groups.find({}, {"_id": 0, "chat_id": 1})]
    except Exception as e:
        print("Group fetch error:", e)
        return []


# ================= STATS =================

def get_total_users():
    try:
        return users.count_documents({})
    except Exception as e:
        print("Count error:", e)
        return 0


def get_active_users(min_messages=1):
    try:
        return users.count_documents({"messages": {"$gte": min_messages}})
    except Exception as e:
        print("Active users error:", e)
        return 0


# ================= LEADERBOARD =================

def get_top_users(limit=10):
    try:
        return list(
            users.find({}, {"_id": 0, "name": 1, "messages": 1})
            .sort("messages", -1)
            .limit(limit)
        )
    except Exception as e:
        print("Top users error:", e)
        return []


# ================= INACTIVE USERS =================

def get_inactive_users(hours=6):
    now = int(time.time())
    gap = hours * 3600

    try:
        return list(
            users.find(
                {"last_active": {"$lt": now - gap}},
                {"_id": 0, "name": 1}
            ).limit(10)
        )
    except Exception as e:
        print("Inactive users error:", e)
        return []


# ================= CLEANUP (🔥 SMART CLEAN) =================

def clean_dead_users():
    """
    Remove users who are useless / blocked bot
    """
    try:
        result = users.delete_many({
            "$or": [
                {"messages": {"$lte": 0}},
                {"user_id": {"$exists": False}}
            ]
        })
        print(f"🧹 Cleaned users: {result.deleted_count}")
    except Exception as e:
        print("Cleanup error:", e)


# ================= USER =================

def get_user(user_id):
    try:
        return users.find_one({"user_id": user_id})
    except Exception as e:
        print("Get user error:", e)
        return None


def delete_user(user_id):
    try:
        users.delete_one({"user_id": user_id})
    except Exception as e:
        print("Delete error:", e)


def clear_history(user_id):
    try:
        users.update_one(
            {"user_id": user_id},
            {"$set": {"history": []}}
        )
    except Exception as e:
        print("Clear history error:", e)