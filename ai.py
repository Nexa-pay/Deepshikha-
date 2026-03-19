import aiohttp
import time
import random
import re
from datetime import datetime
import pytz

from config import (
    OPENROUTER_API_KEY,
    MODEL,
    TEMPERATURE,
    MAX_TOKENS
)

from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= TIME =================

def is_night():
    india = pytz.timezone("Asia/Kolkata")
    return datetime.now(india).hour in range(23, 24) or datetime.now(india).hour in range(0, 6)


# ================= NAME CLEAN =================

def clean_name(name):
    if not name:
        return None

    name = re.sub(r'[^a-zA-Z ]', '', name).strip()
    return name if len(name) >= 3 else None


# ================= IMAGE =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]


def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])


def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= TYPE =================

def detect_type(text):
    t = text.lower()

    if any(x in t for x in ["love", "miss", "baby", "jaan"]):
        return "flirty"

    if any(x in t for x in ["why", "what", "kaise", "kya"]):
        return "question"

    if len(t.split()) <= 2:
        return "dry"

    return "normal"


# ================= SECRET MEMORY =================

def extract_secrets(text):
    text = text.lower()
    secrets = []

    if len(text.split()) < 4:
        return secrets

    if any(x in text for x in ["gf", "bf", "breakup"]):
        secrets.append({"type": "relationship", "value": text})

    if any(x in text for x in ["sad", "alone", "hurt"]):
        secrets.append({"type": "emotion", "value": text})

    if any(x in text for x in ["i like", "mujhe pasand"]):
        secrets.append({"type": "like", "value": text})

    return secrets


# ================= CLEAN =================

def clean_reply(reply):
    reply = re.sub(r"\*.*?\*", "", reply)
    reply = re.sub(r"\(.*?\)", "", reply)
    reply = re.sub(r"\s+", " ", reply).strip()
    return reply


# ================= ANTI-RUDE FILTER =================

def fix_tone(reply):
    bad_words = ["bakchodi", "chup chaap", "rona band", "chal nikal"]

    if any(w in reply.lower() for w in bad_words):
        return random.choice([
            "itna attitude kyun 😏",
            "aise mat bolo na 😌",
            "tum thode rude ho 😒"
        ])

    return reply


# ================= SHORT CONTROL =================

def smart_short(reply):
    reply = reply.split("\n")[0]
    words = reply.split()

    # trim instead of replacing (natural feel)
    return " ".join(words[:10])


# ================= MAIN =================

async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()
        safe_name = clean_name(name)
        night = is_night()

        # 🔒 OWNER
        if "owner" in text_lower:
            return "owner ko chhodo… mujhpe focus karo 😏"

        # 🔒 NAME
        if any(x in text_lower for x in ["mera naam", "my name"]):
            return "naam toh yaad hai mujhe 😏"

        # 🔥 STICKER DEMAND STYLE
        if "sticker" in text_lower:
            return random.choice([
                "sirf sticker hi chahiye tumhe 😏",
                "khud nahi bhejoge kya 😌",
                "itni demand kyun 😏"
            ])

        user_data = users.find_one({"user_id": user_id}) or {}

        history = user_data.get("history", [])
        secrets = user_data.get("secrets", [])
        relationship = int(user_data.get("relationship", 0))
        last_seen = user_data.get("last_seen", int(time.time()))

        now = int(time.time())
        gap = now - last_seen

        msg_type = detect_type(text)

        # RELATIONSHIP ENGINE
        if msg_type == "flirty":
            relationship += 6
        elif msg_type == "dry":
            relationship += 1
        else:
            relationship += 2

        if gap > 3600:
            relationship -= 2

        relationship = max(0, min(200, relationship))

        # ================= MOOD =================

        if relationship > 120:
            mood = "possessive flirty"
        elif relationship > 70:
            mood = "playful flirty"
        else:
            mood = "teasing"

        if night:
            mood += ", soft romantic"

        # ================= MEMORY =================

        new_secrets = extract_secrets(text)

        if new_secrets:
            users.update_one(
                {"user_id": user_id},
                {"$push": {"secrets": {"$each": new_secrets, "$slice": -20}}}
            )

        secret_text = ""
        for s in secrets[-3:]:
            if isinstance(s, dict):
                secret_text += f"- {s.get('value')}\n"

        # ================= PROMPT =================

        system_prompt = f"""
You are ALWAYS a real Indian girl chatting.

STRICT RULES:
- always female
- never say you are AI
- 1 short reply only
- Hinglish only
- no explanation
- no roleplay (*)
- no long text

STYLE:
- flirty, teasing, natural
- confuse + attract
- never give direct answers

MOOD: {mood}

MEMORY:
{secret_text}
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-15:]:
            if isinstance(h, dict):
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("text")})
                elif h.get("role") == "bot":
                    messages.append({"role": "assistant", "content": h.get("text")})

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
                try:
                    result = await res.json()
                except:
                    return "network slow hai 😌"

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya 😏"

        # ================= FINAL PROCESS =================

        reply = clean_reply(reply)
        reply = fix_tone(reply)
        reply = smart_short(reply)

        # ================= SAVE =================

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "relationship": relationship,
                    "last_seen": now
                },
                "$push": {
                    "history": {
                        "$each": [
                            {"role": "user", "text": text},
                            {"role": "bot", "text": reply}
                        ],
                        "$slice": -40
                    }
                }
            },
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "network slow hai 😌"
        
        # ================= MOOD DETECT =================

def detect_reply_mood(reply):
    try:
        r = reply.lower()

        if any(x in r for x in ["love", "miss", "jaan"]):
            return "love"

        if any(x in r for x in ["sad", "alone", "hurt", "cry"]):
            return "cry"

        if any(x in r for x in ["kiss", "mwah"]):
            return "kiss"

        if any(x in r for x in ["angry", "attitude", "ignore"]):
            return "angry"

        return "cute"

    except:
        return "cute"