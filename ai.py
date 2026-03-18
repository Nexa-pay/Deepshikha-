import aiohttp
import time
import random

from config import (
    OPENROUTER_API_KEY,
    MODEL,
    TEMPERATURE,
    MAX_TOKENS
)

from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= IMAGE SYSTEM =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]


def should_send_image(text):
    triggers = ["photo", "pic", "selfie", "send pic", "image"]
    return any(t in text.lower() for t in triggers)


def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= REPLY → MOOD =================

def detect_reply_mood(reply):
    r = reply.lower()

    if any(x in r for x in ["miss", "love", "jaan"]):
        return "love"

    if any(x in r for x in ["sad", "alone", "hurt"]):
        return "cry"

    if any(x in r for x in ["kiss"]):
        return "kiss"

    if any(x in r for x in ["angry", "ignore", "attitude"]):
        return "angry"

    if any(x in r for x in ["haha", "lol"]):
        return "cute"

    return "cute"


# ================= INTENSITY =================

def detect_intensity(reply):
    r = reply.lower()

    if any(x in r for x in ["bohot", "bahut", "so much", "really", "very"]):
        return "intense"

    return "light"


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
        text_lower = text.lower()

        # 🔥 OWNER PROTECTION
        if "owner" in text_lower:
            return random.choice([
                "owner ka kya karoge 😏",
                "main hu na… owner chhodo 😌",
                "itni curiosity kyun hai 😏"
            ])

        # 🔥 NAME DIRECT ANSWER (NO AI GUESS)
        if "mera naam" in text_lower or "my name" in text_lower:
            return f"tumhara naam {name} hai 😏"

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
            comeback = "you noticed they were gone and missed them slightly"
        elif gap > 21600:
            comeback = "you noticed absence, slight attitude"
        elif gap > 3600:
            comeback = "soft warm comeback"
        else:
            comeback = "normal flow"

        # ================= POSSESSIVE =================

        possessive_hint = ""

        if relationship > 80 and msg_type == "flirty":
            possessive_hint = "slight possessive teasing tone"
        elif ignore_count > 5:
            possessive_hint = "feels ignored, mild attitude"

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

IMPORTANT:
- User name is {name}
- NEVER guess or change name
- NEVER reveal bot owner

Rules:
- Short reply (1 line)
- Hinglish only
- Natural human tone

Personality:
- calm, confident
- slightly flirty
- {mood}

Behavior:
- remember chats
- react to absence
- slight attitude if ignored

Comeback: {comeback}
Tone: {possessive_hint}
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
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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