import os
import time
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# ================= CONNECTION =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )

    db = client["telegram_bot"]

    users = db["users"]
    groups = db["groups"]

    # INDEXES
    users.create_index("user_id", unique=True)
    users.create_index("last_active")
    users.create_index("messages")
    groups.create_index("chat_id", unique=True)

    print("Database connected successfully 🚀")

except ServerSelectionTimeoutError:
    print("❌ MongoDB connection failed")
    raise


# ================= UPDATE USER =================

def update_user(user_id, name):
    now = int(time.time())

    try:
        users.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "messages": 0,
                    "last_seen": now,
                    "attachment": 0,
                    "relationship": 0,
                    "ignore_count": 0,
                    "personality": {"type": "normal"},
                    "favorites": {"topics": []},
                    "history": [],
                    "secrets": [],
                    "tokens": 20,
                    "is_vip": False,
                    "vip_expiry": 0,
                    "trial_used": False,
                    "trial_expiry": 0,
                    "ref_by": None,
                    "ref_count": 0,
                    "last_sticker": None
                },

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


# ================= GROUP =================

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
    except:
        return []


# ================= TOKENS =================

def use_tokens(user_id, amount):
    user = users.find_one({"user_id": user_id})

    if not user:
        return False

    if user.get("tokens", 0) < amount:
        return False

    users.update_one(
        {"user_id": user_id},
        {"$inc": {"tokens": -amount}}
    )

    return True


# ================= VIP =================

def give_vip(user_id, days=30):
    expiry = int(time.time()) + (days * 86400)

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "is_vip": True,
                "vip_expiry": expiry
            }
        }
    )


def is_vip_user(user):
    return user.get("is_vip") and user.get("vip_expiry", 0) > time.time()


# ================= TRIAL =================

def give_trial(user_id):
    expiry = int(time.time()) + (30 * 86400)

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "trial_used": True,
                "trial_expiry": expiry
            }
        }
    )


def has_access(user):
    now = time.time()

    if user.get("is_vip") and user.get("vip_expiry", 0) > now:
        return True

    if user.get("trial_expiry", 0) > now:
        return True

    return False


# ================= LEADERBOARD =================

def get_top_users(limit=10):
    try:
        return list(
            users.find({}, {"_id": 0, "name": 1, "messages": 1})
            .sort("messages", -1)
            .limit(limit)
        )
    except:
        return []