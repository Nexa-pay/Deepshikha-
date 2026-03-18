import aiohttp
import time
import random

from config import (
    OPENROUTER_API_KEY,
    MODEL,
    TEMPERATURE,
    MAX_TOKENS,
    PHOTO_CHANCE
)

from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= IMAGE SYSTEM =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4818.jpg",
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]


def should_send_image(text):
    triggers = ["photo", "pic", "selfie", "send pic", "image"]
    return any(t in text.lower() for t in triggers)


def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= MESSAGE TYPE =================

def detect_type(text):
    text = text.lower()

    if any(x in text for x in ["love", "miss", "baby", "jaan"]):
        return "flirty"
    elif any(x in text for x in ["why", "what", "who", "kaise", "kya"]):
        return "question"
    elif len(text.split()) <= 2:
        return "dry"
    else:
        return "normal"


# ================= PERSONALITY =================

def analyze_user(text):
    text = text.lower()

    personality = "normal"
    topics = []

    if any(x in text for x in ["love", "miss", "baby", "jaan"]):
        personality = "flirty"
        topics.append("love")

    elif any(x in text for x in ["sad", "alone", "hurt"]):
        personality = "emotional"
        topics.append("emotions")

    elif any(x in text for x in ["money", "earn", "business"]):
        topics.append("money")

    elif len(text.split()) <= 2:
        personality = "dry"

    return personality, topics


# ================= TIME GAP =================

def get_gap(last_time):
    try:
        if not last_time:
            return 0
        if isinstance(last_time, str):
            last_time = int(last_time)
        return int(time.time()) - last_time
    except:
        return 0


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        relationship = user_data.get("relationship", 0)
        ignore_count = user_data.get("ignore_count", 0)

        history = user_data.get("history", [])
        last_seen = user_data.get("last_seen")

        personality_data = user_data.get("personality", {})
        fav_data = user_data.get("favorites", {})

        now = int(time.time())
        gap = get_gap(last_seen)

        msg_type = detect_type(text)
        personality, topics = analyze_user(text)

        # ================= RELATIONSHIP =================

        if msg_type == "flirty":
            attachment += 5
            relationship += 5
        elif msg_type == "dry":
            attachment += 1
            relationship += 1
            ignore_count += 1
        else:
            attachment += 2
            relationship += 2

        # ================= MOOD =================

        if relationship > 100:
            mood = "emotionally attached, slightly possessive"
        elif relationship > 50:
            mood = "soft flirty, interested"
        else:
            mood = "calm neutral"

        # ================= COMEBACK =================

        if gap > 86400:
            comeback = "you noticed they were gone and slightly missed them"
        elif gap > 21600:
            comeback = "you noticed absence, slight attitude"
        elif gap > 3600:
            comeback = "soft warm comeback"
        else:
            comeback = "normal flow"

        # ================= POSSESSIVE =================

        possessive_hint = ""

        if relationship > 80 and msg_type == "flirty":
            possessive_hint = "use slight possessive teasing tone"
        elif ignore_count > 5:
            possessive_hint = "you feel ignored, show mild attitude"

        # ================= USER PROFILE =================

        user_type = personality_data.get("type", "normal")
        fav_topics = ", ".join(fav_data.get("topics", []))

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

CORE RULES:
- Reply ONLY based on user's message
- Continue conversation naturally
- Keep reply SHORT (1 line)
- Hinglish only

STRICT:
- Never rude
- Never abusive
- Soft, natural, slightly flirty

CONFUSION:
- unclear → playful + flirty

MOOD: {mood}
USER TYPE: {user_type}
FAV TOPICS: {fav_topics}
COMEBACK: {comeback}
POSSESSIVE: {possessive_hint}
"""

        # ================= BUILD HISTORY =================

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-15:]:
            if h.startswith("User:"):
                messages.append({"role": "user", "content": h[6:]})
            elif h.startswith("Bot:"):
                messages.append({"role": "assistant", "content": h[5:]})

        messages.append({"role": "user", "content": text})

        # ================= API =================

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY},
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya… thoda clear bolo 😌"

        reply = reply.strip()

        # ================= SAVE =================

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "attachment": attachment,
                    "relationship": relationship,
                    "ignore_count": ignore_count,
                    "last_seen": now,
                    "personality.type": personality
                },
                "$addToSet": {
                    "favorites.topics": {"$each": topics}
                },
                "$push": {
                    "history": {
                        "$each": [
                            f"User: {text}",
                            f"Bot: {reply}"
                        ],
                        "$slice": -25
                    }
                }
            },
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "clear nahi hua… thoda aur clearly bolo 😌"


# ================= TAG MESSAGE =================

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": f"Write 1 short Hinglish recall line for {name}"}
            ],
            "temperature": 0.7,
            "max_tokens": 30
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        return result.get("choices", [{}])[0].get("message", {}).get("content", f"{name} kaha ho").strip()

    except:
        return f"{name} kaha ho"