import aiohttp
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


# ================= QUESTION DETECT =================
def is_question(text):
    t = text.lower()
    return (
        "?" in t or
        any(k in t for k in [
            "who","what","when","where","why","how",
            "kaun","kya","kab","kaha","kaise",
            "pm","president","capital","india"
        ])
    )


# ================= CLEAN =================
def clean_reply(reply):
    reply = re.sub(r"\*.*?\*", "", reply)
    reply = re.sub(r"\(.*?\)", "", reply)
    return re.sub(r"\s+", " ", reply).strip()


def short_reply(reply):
    return " ".join(reply.split()[:12])


# ================= MAIN =================
async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}
        history = user_data.get("history", [])
        last_reply = user_data.get("last_reply", "")

        # ================= MODE =================
        if is_question(text):
            system_prompt = """
You are a smart Indian girl.

RULES:
- Answer correctly
- Add slight natural tone
- Hinglish only
- Max 12 words
- No explanation
"""
        else:
            system_prompt = """
You are a real Indian girl chatting.

RULES:
- Natural reply
- Relevant to message
- Hinglish only
- Max 12 words
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-10:]:
            if isinstance(h, dict):
                messages.append({
                    "role": "assistant" if h.get("role") == "bot" else "user",
                    "content": h.get("text")
                })

        messages.append({"role": "user", "content": text})

        # ================= API CALL WITH RETRY =================
        reply = None

        for _ in range(2):
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
                        continue

                    result = await res.json()
                    reply = result.get("choices", [{}])[0].get("message", {}).get("content")

                    if reply:
                        break

        # ================= FALLBACK =================
        if not reply:
            return random.choice([
                "samajh nahi aaya… phir bolo 😌",
                "thoda clear bolo na 😏",
                "tum confusing ho 😄"
            ])

        reply = clean_reply(reply)
        reply = short_reply(reply)

        # ================= SOFT ANTI-REPEAT =================
        if reply == last_reply:
            reply += random.choice([" 😏", " hmm", " acha"])

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
        return "thoda issue hai… phir try karo 😌"


# ================= MOOD DETECT =================
def detect_reply_mood(reply):
    return "cute"