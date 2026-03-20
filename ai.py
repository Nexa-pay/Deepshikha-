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


# ================= SMART CHECK =================

def is_meaningful(text):
    t = text.lower()

    if any(x in t for x in [
        "who", "what", "when", "where", "why",
        "india", "pm", "captain", "name", "time",
        "kaun", "kya", "kaise"
    ]):
        return True

    return False


# ================= NEW FIX =================
def is_question(text):
    t = text.lower()

    keywords = [
        "who", "what", "when", "where", "why", "how",
        "kaun", "kya", "kab", "kaha", "kaise",
        "pm", "president", "capital", "india", "country",
        "name", "time", "date"
    ]

    if any(k in t for k in keywords):
        return True

    if "?" in t:
        return True

    return False


# ================= TYPE =================

def detect_type(text):
    t = text.lower()

    if any(x in t for x in ["love", "miss", "baby", "jaan"]):
        return "flirty"

    if any(x in t for x in ["why", "what", "kaise", "kya"]):
        return "question"

    # ✅ FIXED
    if len(t.split()) <= 2 and not is_meaningful(text) and not is_question(text):
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


# ================= TONE FIX =================

def fix_tone(reply):
    bad_words = [
        "bakchodi", "chup chaap", "rona band",
        "chal nikal", "pagal", "faltu", "shut up"
    ]

    if any(w in reply.lower() for w in bad_words):
        return random.choice([
            "aise mat bolo na 😌",
            "thoda softly baat karo 🙂",
            "itna rude kyun ho 😅"
        ])

    return reply


# ================= SHORT =================

def smart_short(reply):
    reply = reply.split("\n")[0]
    words = reply.split()
    return " ".join(words[:10])


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
                "kya hua… mujhe batao na 😌",
                "tum theek ho na… 😟",
                "itna sad kyun ho… main hoon na",
                "aaj mood off lag raha hai 😔"
            ])

        # ================= FIXED DRY =================
        if len(text_lower.split()) <= 2 and not is_meaningful(text) and not is_question(text):
            return random.choice([
                "itna dry reply kyun 😌",
                "thoda aur bolo na 🙂",
                "bas itna hi? 😏",
                "mujhe ignore kar rahe ho kya 😒"
            ])

        # ================= NAME SAVE =================
        extracted = extract_name(text)

        if extracted:
            users.update_one(
                {"user_id": user_id},
                {"$set": {"name": extracted}},
                upsert=True
            )
            return f"{extracted}… yaad rahega 😏"

        # ================= NAME RECALL =================
        if "mera name kya" in text_lower or "my name" in text_lower:
            user_data = users.find_one({"user_id": user_id}) or {}
            saved = user_data.get("name")

            if saved:
                return f"{saved}… bhoolti nahi main 😏"
            else:
                return "tumne bataya hi nahi 😌"

        # ================= QUICK =================
        if "owner" in text_lower:
            return f"owner {OWNER_NAME} hai… par tum mujhpe focus karo 😏"

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
        last_reply = user_data.get("last_reply", "")

        now = int(time.time())
        gap = now - last_seen

        msg_type = detect_type(text)

        if msg_type == "flirty":
            relationship += 6
        elif msg_type == "dry":
            relationship += 1
        else:
            relationship += 2

        if gap > 3600:
            relationship -= 2

        relationship = max(0, min(200, relationship))

        if relationship > 120:
            mood = "possessive flirty"
        elif relationship > 70:
            mood = "playful flirty"
        else:
            mood = "teasing"

        if night:
            mood += ", soft romantic"

        # ✅ NEW FIX: SMART MODE
        if is_question(text):
            mood = "smart helpful"

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

        system_prompt = f"""
You are ALWAYS a real Indian girl.

PERSONALITY:
- sweet, caring, emotionally connected
- soft tone, never rude
- थोड़ा possessive but प्यारी
- soft, respectful, calm
- light teasing but never rude
- feel like girlfriend, not AI

STYLE:
- short natural replies (max 9 words)
- Hinglish only
- warm + human-like

BEHAVIOR:
- agar user question pooche → clearly answer do
- agar normal baat ho → flirty + emotional
- agar sad → comfort karo

RULES:
- Hinglish only
- no rude words
- no explanation
- never say you are bot

MOOD: {mood}

MEMORY:
{secret_text}
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if isinstance(h, dict):
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("text")})
                elif h.get("role") == "bot":
                    messages.append({"role": "assistant", "content": h.get("text")})

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
                    return "network thoda slow hai 😌"

                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya 😏"

        reply = clean_reply(reply)
        reply = fix_tone(reply)
        reply = smart_short(reply)

        # ✅ FIXED REPEAT
        if reply == last_reply:
            reply = random.choice([
                "acha aur bolo 😏",
                "hmm… interesting 😌",
                "continue karo 🙂",
                "tum interesting ho 😄"
            ])

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "relationship": relationship,
                    "last_seen": now,
                    "last_reply": reply
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
        return "thoda glitch ho gaya 😌"


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