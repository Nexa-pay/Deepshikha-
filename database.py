import os
import time
import re
import random
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

    print("✅ Database connected successfully 🚀")

except ServerSelectionTimeoutError:
    print("❌ MongoDB connection failed")
    raise


# ================= ENSURE USER =================

def ensure_user(user_id, name="user"):
    now = int(time.time())

    users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "saved_name": None,
                "history": [],
                "nicknames": [],
                "last_nickname": None,
                "tokens": 20,
                "is_vip": False,
                "vip_expiry": 0,
                "trial_used": False,
                "trial_expiry": 0,
                "messages": 0
            },
            "$set": {
                "name": name,
                "display_name": name,
                "last_active": now,
                "last_seen": now
            }
        },
        upsert=True
    )


# ================= UPDATE USER =================

def update_user(user_id, name):
    try:
        ensure_user(user_id, name)

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name if name else "user",
                    "display_name": name if name else "user",
                    "last_active": int(time.time())
                },
                "$inc": {"messages": 1}
            }
        )

    except Exception as e:
        print("❌ DB update error:", e)


# ================= CHAT MEMORY =================

def save_chat(user_id, role, text, limit=20):
    try:
        users.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "history": {
                        "$each": [{
                            "role": role,
                            "text": text,
                            "time": int(time.time())
                        }],
                        "$slice": -limit
                    }
                }
            }
        )
    except Exception as e:
        print("❌ Chat save error:", e)


def get_chat_history(user_id):
    user = users.find_one({"user_id": user_id})
    return user.get("history", []) if user else []


# ================= NAME =================

def extract_name(text):
    patterns = [
        r"mera naam (\w+)",
        r"mera name (\w+)",
        r"my name is (\w+)"
    ]
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            return m.group(1).capitalize()
    return None


def save_user_name(user_id, name):
    ensure_user(user_id)
    users.update_one(
        {"user_id": user_id},
        {"$set": {"saved_name": name}}
    )


def get_saved_name(user_id):
    user = users.find_one({"user_id": user_id})
    return user.get("saved_name") if user else None


# ================= NICKNAME =================

def extract_nickname(text):
    patterns = [
        r"mujhe (\w+) bulao",
        r"call me (\w+)"
    ]
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            return m.group(1).capitalize()
    return None


def save_nickname(user_id, nickname):
    ensure_user(user_id)

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {"last_nickname": nickname},
            "$addToSet": {"nicknames": nickname}
        }
    )


def get_nickname(user_id):
    user = users.find_one({"user_id": user_id})
    return user.get("last_nickname") if user else None


# ================= MEMORY =================

def extract_age(text):
    m = re.search(r"(\d{1,2}) (saal|years?)", text.lower())
    return int(m.group(1)) if m else None


def extract_mood(text):
    moods = {
        "sad": ["sad", "dukhi", "udaas"],
        "happy": ["happy", "khush"],
        "angry": ["gussa", "angry"],
        "love": ["pyaar", "love"]
    }

    for mood, words in moods.items():
        if any(w in text.lower() for w in words):
            return mood
    return None


def save_memory(user_id, age=None, mood=None):
    update = {}
    if age:
        update["age"] = age
    if mood:
        update["mood"] = mood

    if update:
        users.update_one({"user_id": user_id}, {"$set": update})


# ================= FLIRTY =================

def flirty_reply(user_id):
    name = get_saved_name(user_id)
    nick = get_nickname(user_id)

    base = nick or name or "tum"

    replies = [
        f"{base}… tum cute ho 😏",
        f"{base}, itna yaad kyun aate ho ❤️",
        f"{base}, main ignore karu ya paas aau? 😏",
        f"Tum dangerous ho {base} 🔥"
    ]

    return random.choice(replies)


# ================= MAIN HANDLER =================

def smart_handler(user_id, text, telegram_name="user"):
    try:
        update_user(user_id, telegram_name)

        # SAVE USER MSG
        save_chat(user_id, "user", text)

        text_l = text.lower()

        # NAME
        name = extract_name(text)
        if name:
            save_user_name(user_id, name)
            reply = f"Acha {name}, yaad rahega 😏"
            save_chat(user_id, "bot", reply)
            return reply

        if "mera naam kya" in text_l:
            name = get_saved_name(user_id)
            reply = f"Tumhara naam {name} hai 😏" if name else "Naam nahi bataya 😅"
            save_chat(user_id, "bot", reply)
            return reply

        # NICKNAME
        nick = extract_nickname(text)
        if nick:
            save_nickname(user_id, nick)
            reply = f"Thik hai… ab tum {nick} ho 😏🔥"
            save_chat(user_id, "bot", reply)
            return reply

        # AGE
        age = extract_age(text)
        if age:
            save_memory(user_id, age=age)
            reply = f"{age}? interesting 😏"
            save_chat(user_id, "bot", reply)
            return reply

        # MOOD
        mood = extract_mood(text)
        if mood:
            save_memory(user_id, mood=mood)
            reply = f"Samajh gayi… tum {mood} ho 💭"
            save_chat(user_id, "bot", reply)
            return reply

        # DEFAULT
        reply = flirty_reply(user_id)
        save_chat(user_id, "bot", reply)
        return reply

    except Exception as e:
        print("❌ Handler error:", e)
        return "Error 😅"


# ================= GROUP =================

def save_group(chat_id):
    groups.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )


def get_groups():
    return [g["chat_id"] for g in groups.find({}, {"_id": 0, "chat_id": 1})]


# ================= HISTORY =================

def clear_history(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$set": {"history": []}}
    )
    return "Chat memory cleared 🧹"
    
    def get_all_users():
    try:
        return [u["user_id"] for u in users.find({}, {"_id": 0, "user_id": 1})]
    except Exception as e:
        print("User fetch error:", e)
        return []