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
    return datetime.now(india).hour >= 23 or datetime.now(india).hour <= 5


# ================= IMAGE =================
IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]

def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])

def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= SMART =================
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
    return re.sub(r"\s+", " ", reply).strip()


# ================= MAIN =================
async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()

        # ================= HARD FACT FIX =================
        if "pm" in text_lower and "india" in text_lower:
            return "Narendra Modi is current Prime Minister of India"

        if "president" in text_lower and "india" in text_lower:
            return "Droupadi Murmu is current President of India"

        # ================= DB =================
        user_data = users.find_one({"user_id": user_id}) or {}
        history = user_data.get("history", [])
        last_reply = user_data.get("last_reply", "")

        # ================= PROMPT =================
        if is_question(text):
            system_prompt = """
You are a helpful assistant.

Answer correctly and clearly.
No flirting.
Short factual reply only.
"""
        else:
            system_prompt = """
You are a normal human.

Reply naturally and relevant to user message.
No random lines.
Short and clean reply.
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
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
                    return "mujhe abhi info nahi mil pa rahi 😔"

                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            return "samajh nahi aaya 🙂"

        reply = clean_reply(reply)

        # ================= ANTI REPEAT =================
        if not is_question(text) and (reply == last_reply):
            reply = "hmm samjha 🙂"

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
        return "thoda issue ho gaya 😔"


# ================= MOOD =================
def detect_reply_mood(reply):
    return "cute"