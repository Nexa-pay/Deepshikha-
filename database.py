import os
import time
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect

# ================= CONNECTION =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        retryWrites=True
    )

    db = client["telegram_bot"]

    users = db["users"]
    groups = db["groups"]

    # 🔥 INDEXES
    users.create_index("user_id", unique=True)
    users.create_index("last_active")
    users.create_index("messages")

    groups.create_index("chat_id", unique=True)

    print("Database connected successfully 🚀")

except ServerSelectionTimeoutError:
    print("❌ MongoDB connection failed")
    raise


# ================= SAFE EXECUTOR =================

def safe_db_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except AutoReconnect:
        print("⚠️ Mongo reconnecting...")
        time.sleep(1)
        return func(*args, **kwargs)
    except Exception as e:
        print("DB error:", e)
        return None


# ================= UPDATE USER =================

def update_user(user_id, name):
    now = int(time.time())

    # 🔥 prevent blank overwrite
    safe_name = name.strip() if name and name.strip() else None

    try:
        users.update_one(
            {"user_id": user_id},
            {
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

                # 🔥 ONLY update name if valid
                "$set": {
                    **({"name": safe_name} if safe_name else {}),
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
    safe_db_call(
        groups.update_one,
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )


def get_groups():
    try:
        return [g["chat_id"] for g in groups.find({}, {"_id": 0, "chat_id": 1})]
    except Exception as e:
        print("Group fetch error:", e)
        return []


# ================= STATS =================

def get_total_users():
    return safe_db_call(users.count_documents, {}) or 0


def get_active_users(min_messages=1):
    return safe_db_call(users.count_documents, {"messages": {"$gte": min_messages}}) or 0


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


# ================= CLEANUP =================

def clean_dead_users():
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
    return safe_db_call(users.find_one, {"user_id": user_id})


def delete_user(user_id):
    safe_db_call(users.delete_one, {"user_id": user_id})


def clear_history(user_id):
    safe_db_call(
        users.update_one,
        {"user_id": user_id},
        {"$set": {"history": []}}
    )