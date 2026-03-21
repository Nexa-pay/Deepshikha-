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


# ================= IMAGE =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]

def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])

def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= SMART =================

def is_meaningful(text):
    t = text.lower()
    return any(x in t for x in [
        "who","what","when","where","why",
        "india","pm","captain","name","time",
        "kaun","kya","kaise"
    ])

def is_question(text):
    t = text.lower()
    return any(k in t for k in [
        "who","what","when","where","why","how",
        "kaun","kya","kab","kaha","kaise",
        "pm","president","capital","india"
    ]) or "?" in t


# ================= CLEAN =================

def clean_reply(reply):
    reply = re.sub(r"\*.*?\*", "", reply)
    reply = re.sub(r"\(.*?\)", "", reply)
    reply = re.sub(r"\s+", " ", reply).strip()
    return reply


def smart_short(reply):
    return " ".join(reply.split()[:12])


# ================= MAIN =================

async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()
        night = is_night()

        # ================= SOFT OVERRIDE =================
        forced_reply = None

        if any(x in text_lower for x in ["sad", "alone", "hurt", "cry"]):
            forced_reply = random.choice([
                "kya hua… mujhe batao na 😌",
                "tum theek ho na… 😟",
                "itna sad kyun ho… main hoon na",
                "aaj mood off lag raha hai 😔"
            ])

        elif len(text_lower.split()) <= 2 and not is_meaningful(text) and not is_question(text):
            forced_reply = random.choice([
                "itna dry reply kyun 😌",
                "thoda aur bolo na 🙂",
                "bas itna hi? 😏",
                "mujhe ignore kar rahe ho kya 😒"
            ])

        user_data = users.find_one({"user_id": user_id}) or {}

        history = user_data.get("history", [])
        relationship = int(user_data.get("relationship", 0))
        last_reply = user_data.get("last_reply", "")

        # ================= PROMPT FIX =================
        if is_question(text):
            system_prompt = """
You are a helpful assistant.

RULES:
- Answer the question correctly
- Give factual answer
- No flirting
- No emotional lines
- Keep it short and clear
"""
        else:
            system_prompt = """
You are a natural human conversational assistant.

RULES:
- Reply only according to user message
- No unrelated lines
- No random flirting
- Keep natural Hinglish tone
- Keep reply short and meaningful
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if isinstance(h, dict):
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("text")})
                elif h.get("role") == "bot":
                    messages.append({"role": "assistant", "content": h.get("text")})

        messages.append({"role": "user", "content": text})

        # ================= API =================
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }, json={
                "model": MODEL,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS
            }) as res:

                if res.status != 200:
                    return "network thoda slow hai 😌"

                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya 😏"

        reply = clean_reply(reply)
        reply = smart_short(reply)

        # ================= ANTI REPEAT FIX =================
        recent = [h.get("text") for h in history[-6:] if h.get("role") == "bot"]

        if reply in recent or reply == last_reply:
            reply = random.choice([
                "acha aur bolo 😏",
                "hmm… interesting 😌",
                "continue karo 🙂",
                "samajh gaya 👍"
            ])

        # ================= FORCED (FIXED) =================
        if forced_reply and not is_question(text):
            reply = forced_reply

        # ================= SAVE =================
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