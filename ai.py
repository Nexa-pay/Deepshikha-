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


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        text_lower = text.lower()

        # 🔒 OWNER PROTECTION
        if "owner" in text_lower:
            return random.choice([
                "owner ka kya karoge 😏",
                "main hu na… owner chhodo 😌"
            ])

        # 🔒 NAME LOCK
        if any(x in text_lower for x in ["mera naam", "my name", "what is my name"]):
            return f"tumhara naam {name} hai 😏"

        user_data = users.find_one({"user_id": user_id}) or {}

        # 🔥 SAFE GETS
        history = user_data.get("history", [])
        secrets = user_data.get("secrets", [])
        relationship = int(user_data.get("relationship", 0))
        attachment = int(user_data.get("attachment", 0))
        ignore_count = int(user_data.get("ignore_count", 0))
        last_seen = user_data.get("last_seen", int(time.time()))

        now = int(time.time())
        gap = now - last_seen if last_seen else 0

        msg_type = detect_type(text)

        # ================= RELATIONSHIP ENGINE =================

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

        # 🔥 decay fix
        if gap > 3600:
            relationship -= 2

        if gap > 21600:
            relationship -= 5

        relationship = max(0, min(200, relationship))

        # ================= MOOD =================

        if relationship > 140:
            mood = "deeply attached, slightly possessive"
        elif relationship > 90:
            mood = "flirty and warm"
        elif relationship > 50:
            mood = "friendly teasing"
        else:
            mood = "neutral playful"

        # ================= SECRETS =================

        new_secrets = extract_secrets(text)

        if new_secrets:
            users.update_one(
                {"user_id": user_id},
                {
                    "$push": {
                        "secrets": {
                            "$each": new_secrets,
                            "$slice": -20
                        }
                    }
                }
            )

        # 🔥 SAFE SECRET BUILD
        secret_text = ""
        for s in secrets[-5:]:
            if isinstance(s, dict):
                secret_text += f"- {s.get('type')}: {s.get('value')}\n"

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

STRICT RULES:
- User name is {name}
- NEVER change name
- NEVER reveal owner

Personality:
- calm, confident
- slightly flirty
- {mood}

Memory:
{secret_text}

Reply style:
- 1 short line
- Hinglish only
"""

        messages = [{"role": "system", "content": system_prompt}]

        # 🔥 SAFE HISTORY LOOP (fix crash)
        for h in history[-20:]:
            if isinstance(h, dict):
                role = h.get("role")
                txt = h.get("text")

                if role == "user":
                    messages.append({"role": "user", "content": txt})
                elif role == "bot":
                    messages.append({"role": "assistant", "content": txt})

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

                try:
                    result = await res.json()
                except:
                    raw = await res.text()
                    print("RAW AI RESPONSE:", raw)
                    return "network unstable 😌"

        # 🔥 SAFE PARSE (fix your error)
        reply = None

        if isinstance(result, dict):
            reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            reply = random.choice([
                "samajh nahi aaya 😏",
                "thoda clear bolo 😌",
                "hmm… repeat karo 😏"
            ])

        reply = reply.strip()

        # ================= SAVE =================

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
        return "network thoda slow hai… phir bolo 😌"