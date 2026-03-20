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
    MAX_TOKENS,
    OWNER_NAME
)

from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= TIME =================

def is_night():
    india = pytz.timezone("Asia/Kolkata")
    hour = datetime.now(india).hour
    return hour >= 23 or hour <= 5


# ================= NAME CLEAN =================

def clean_name(name):
    if not name:
        return None
    name = re.sub(r'[^a-zA-Z ]', '', name).strip()
    return name if len(name) >= 3 else None


# ================= NAME EXTRACT =================

def extract_name(text):
    text = text.lower()

    patterns = [
        r"mera naam (\w+)",
        r"my name is (\w+)",
        r"i am (\w+)",
        r"main (\w+) hu"
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return clean_name(match.group(1))

    return None


# ================= IMAGE =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]

def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])

def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= SMART TYPE =================

def is_meaningful(text):
    t = text.lower()

    # real queries / meaningful words
    if any(x in t for x in [
        "who", "what", "when", "where", "why",
        "india", "pm", "captain", "name", "time",
        "kaun", "kya", "kaise"
    ]):
        return True

    return False


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


# ================= SHORT =================

def smart_short(reply):
    reply = reply.split("\n")[0]
    words = reply.split()
    return " ".join(words[:12])


# ================= VARIATION =================

def add_variation(reply):
    return reply + random.choice([
        "",
        " 😌",
        " hmm",
        " acha",
        " na",
        " tum bhi na",
        " seriously?"
    ])


# ================= MAIN =================

async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()
        night = is_night()

        # ================= SAD =================
        if any(x in text_lower for x in ["sad", "alone", "hurt", "cry"]):
            return random.choice([
                "kya hua… batao na 😌",
                "main hoon na… tension mat lo",
                "itna sad kyun ho… 😔",
                "tum theek ho na?"
            ])

        # ================= SMART DRY =================
        if len(text_lower.split()) <= 2 and not is_meaningful(text):
            return random.choice([
                "hmm… kuch aur bolo 😏",
                "bas itna hi? 🙂",
                "thoda aur bolo na 😌",
                "itne chup kyun ho 😄"
            ])

        # ================= NAME =================
        extracted = extract_name(text)

        if extracted:
            users.update_one(
                {"user_id": user_id},
                {"$set": {"name": extracted}},
                upsert=True
            )
            return f"{extracted}… yaad rahega 😏"

        if "mera name kya" in text_lower or "my name" in text_lower:
            user_data = users.find_one({"user_id": user_id}) or {}
            saved = user_data.get("name")

            if saved:
                return f"{saved}… bhoolti nahi main 😏"
            else:
                return "tumne bataya hi nahi 😌"

        # ================= QUICK =================
        if "owner" in text_lower:
            return f"owner {OWNER_NAME} hai… par tum important ho 😏"

        user_data = users.find_one({"user_id": user_id}) or {}

        history = user_data.get("history", [])
        relationship = int(user_data.get("relationship", 0))
        last_reply = user_data.get("last_reply", "")

        # ================= MOOD =================
        if relationship > 120:
            mood = "possessive flirty"
        elif relationship > 70:
            mood = "playful flirty"
        else:
            mood = "teasing"

        if night:
            mood += ", soft romantic"

        # ================= PROMPT =================
        system_prompt = f"""
You are a real Indian girl.

- Hinglish only
- short natural replies
- flirty + caring + human
- never repetitive
- always slightly different replies

MOOD: {mood}
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-8:]:
            messages.append({
                "role": "user" if h["role"] == "user" else "assistant",
                "content": h["text"]
            })

        messages.append({"role": "user", "content": text})

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
                if res.status != 200:
                    return "network slow hai 😌"

                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya 😏"

        reply = clean_reply(reply)
        reply = smart_short(reply)

        # ================= STRONG ANTI-REPEAT =================
        if reply == last_reply:
            alt = [
                "tum interesting ho 😏",
                "acha aur bolo 🙂",
                "hmm… sun rahi hoon 😌",
                "continue karo na 😄"
            ]
            reply = random.choice(alt)

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {"last_reply": reply},
                "$push": {
                    "history": {
                        "$each": [
                            {"role": "user", "text": text},
                            {"role": "bot", "text": reply}
                        ],
                        "$slice": -30
                    }
                }
            },
            upsert=True
        )

        return add_variation(reply)

    except Exception as e:
        print("AI ERROR:", e)
        return "thoda glitch ho gaya 😌"


# ================= MOOD DETECT =================

def detect_reply_mood(reply):
    r = reply.lower()

    if "love" in r:
        return "love"
    if "sad" in r:
        return "cry"
    if "kiss" in r:
        return "kiss"
    if "angry" in r:
        return "angry"

    return "cute"