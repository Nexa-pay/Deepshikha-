import aiohttp
import time
import random
import re

from config import (
    OPENROUTER_API_KEY,
    MODEL,
    TEMPERATURE,
    MAX_TOKENS
)

from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= NAME CLEANER =================

def clean_name(name):
    if not name:
        return None

    name = re.sub(r'[^a-zA-Z ]', '', name).strip()

    if len(name) < 3:
        return None

    return name


# ================= IMAGE =================

IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]


def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])


def get_random_image():
    return random.choice(IMAGE_URLS)


# ================= MOOD =================

def detect_reply_mood(reply):
    try:
        r = reply.lower()

        if any(x in r for x in ["love", "miss", "baby", "jaan"]):
            return "love"

        if any(x in r for x in ["sad", "cry", "alone", "hurt"]):
            return "cry"

        if any(x in r for x in ["kiss", "mwah"]):
            return "kiss"

        if any(x in r for x in ["angry", "attitude", "ignore"]):
            return "angry"

        return random.choice(["cute", "love"])

    except:
        return "cute"


# ================= TYPE =================

def detect_type(text):
    try:
        t = text.lower()

        if any(x in t for x in ["love", "miss", "baby", "jaan"]):
            return "flirty"

        if any(x in t for x in ["why", "what", "kaise", "kya"]):
            return "question"

        if len(t.split()) <= 2:
            return "dry"

        return "normal"

    except:
        return "normal"


# ================= SECRET MEMORY =================

def extract_secrets(text):
    try:
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

        if any(x in text for x in ["exam", "job", "college"]):
            secrets.append({"type": "life", "value": text})

        return secrets

    except:
        return []


# ================= CLEAN REPLY =================

def clean_reply(reply):
    # ❌ remove roleplay (*smiles*)
    reply = re.sub(r"\*.*?\*", "", reply)

    # remove weird spacing
    reply = re.sub(r"\s+", " ", reply).strip()

    return reply


# ================= FORCE SHORT =================

def force_short_reply(reply):
    words = reply.split()

    if len(words) > 12:
        return random.choice([
            "itna long kyun bol rahe ho 😏",
            "short me bolo na 😌",
            "seedha point pe aao 😏"
        ])

    return reply


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()
        safe_name = clean_name(name)

        # OWNER PROTECTION
        if "owner" in text_lower:
            return random.choice([
                "owner ka kya karoge 😏",
                "main hu na… owner chhodo 😌"
            ])

        # NAME RESPONSE
        if any(x in text_lower for x in ["mera naam", "my name", "what is my name"]):
            if safe_name:
                return f"tumhara naam {safe_name} hai 😏"
            return "naam thoda unique hai tumhara 😏"

        user_data = users.find_one({"user_id": user_id}) or {}

        history = user_data.get("history", [])
        secrets = user_data.get("secrets", [])
        relationship = int(user_data.get("relationship", 0))
        attachment = int(user_data.get("attachment", 0))
        ignore_count = int(user_data.get("ignore_count", 0))
        last_seen = user_data.get("last_seen", int(time.time()))

        now = int(time.time())
        gap = now - last_seen if last_seen else 0

        msg_type = detect_type(text)

        # RELATIONSHIP ENGINE
        if msg_type == "flirty":
            attachment += 6
            relationship += 6
        elif msg_type == "question":
            attachment += 3
            relationship += 2
        elif msg_type == "dry":
            attachment += 1
            relationship += 1
            ignore_count += 1
        else:
            attachment += 2
            relationship += 2

        if gap > 3600:
            relationship -= 2
        if gap > 21600:
            relationship -= 5

        relationship = max(0, min(200, relationship))

        # MOOD
        if relationship > 140:
            mood = "deeply attached"
        elif relationship > 90:
            mood = "flirty"
        elif relationship > 50:
            mood = "friendly"
        else:
            mood = "neutral"

        # SAVE SECRETS
        new_secrets = extract_secrets(text)

        if new_secrets:
            users.update_one(
                {"user_id": user_id},
                {"$push": {"secrets": {"$each": new_secrets, "$slice": -20}}}
            )

        # SECRET TEXT
        secret_text = ""
        for s in secrets[-5:]:
            if isinstance(s, dict):
                secret_text += f"- {s.get('value')}\n"

        # SYSTEM PROMPT (STRICT)
        system_prompt = f"""
You are a real girl chatting on Telegram.

Tone: {mood}

STRICT RULES:
- Only 1 short line reply
- Max 8-10 words
- Hinglish only
- No roleplay actions (*)
- No long text
- No paragraphs
- Do not use user's name unless needed

Examples:
- Kya hua? Itne chup kyun ho 😏
- Mujhe ignore kar rahe ho kya 😒
- Aaj mood off lag raha hai 😌

Memory:
{secret_text}
"""

        messages = [{"role": "system", "content": system_prompt}]

        for h in history[-20:]:
            if isinstance(h, dict):
                if h.get("role") == "user":
                    messages.append({"role": "user", "content": h.get("text")})
                elif h.get("role") == "bot":
                    messages.append({"role": "assistant", "content": h.get("text")})

        messages.append({"role": "user", "content": text})

        # API CALL
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
                    return "network issue 😌"

        reply = None

        if isinstance(result, dict):
            reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = "samajh nahi aaya 😏"

        # CLEAN + SHORT
        reply = clean_reply(reply)
        reply = force_short_reply(reply)

        # SAVE HISTORY
        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "attachment": attachment,
                    "relationship": relationship,
                    "ignore_count": ignore_count,
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