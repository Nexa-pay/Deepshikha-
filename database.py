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

                # 🔥 ONLY HERE → NO CONFLICT EVER
                "$inc": {
                    "messages": 1
                }
            },
            upsert=True
        )

    except Exception as e:
        print("DB update error:", e)


# ================= SAFE WRAPPER =================

def safe_update_user(user_id, name):
    try:
        update_user(user_id, name)
    except Exception as e:
        print("Safe update error:", e)


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
    except Exception as e:
        print("Group fetch error:", e)
        return []


# ================= TOKENS =================

def use_tokens(user_id, amount):
    try:
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

    except Exception as e:
        print("Token error:", e)
        return False


def add_tokens(user_id, amount):
    try:
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"tokens": amount}}
        )
    except Exception as e:
        print("Add token error:", e)


# ================= VIP =================

def give_vip(user_id, days=30):
    expiry = int(time.time()) + (days * 86400)

    try:
        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_vip": True,
                    "vip_expiry": expiry
                }
            }
        )
    except Exception as e:
        print("VIP error:", e)


def is_vip_user(user):
    try:
        return bool(user and user.get("is_vip") and user.get("vip_expiry", 0) > time.time())
    except:
        return False


# ================= TRIAL =================

def give_trial(user_id):
    expiry = int(time.time()) + (30 * 86400)

    try:
        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "trial_used": True,
                    "trial_expiry": expiry
                }
            }
        )
    except Exception as e:
        print("Trial error:", e)


def has_access(user):
    try:
        now = time.time()

        if not user:
            return False

        if user.get("is_vip") and user.get("vip_expiry", 0) > now:
            return True

        if user.get("trial_expiry", 0) > now:
            return True

        return False

    except Exception as e:
        print("Access error:", e)
        return False


# ================= REFERRAL SYSTEM =================

def add_referral(new_user_id, referrer_id):
    try:
        if new_user_id == referrer_id:
            return

        users.update_one(
            {"user_id": new_user_id},
            {"$set": {"ref_by": referrer_id}},
            upsert=True
        )

        users.update_one(
            {"user_id": referrer_id},
            {
                "$inc": {"ref_count": 1, "tokens": 5}
            }
        )

    except Exception as e:
        print("Referral error:", e)


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