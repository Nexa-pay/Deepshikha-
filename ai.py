import aiohttp
import time
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


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


# ================= TIME GAP =================

def get_gap(last_time):
    if not last_time:
        return 0
    return int(time.time()) - last_time


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        history = user_data.get("history", [])
        last_seen = user_data.get("last_seen")

        now = int(time.time())
        gap = get_gap(last_seen)

        msg_type = detect_type(text)

        # ================= ATTACHMENT =================

        if msg_type == "flirty":
            attachment += 5
        elif msg_type == "dry":
            attachment += 1
        else:
            attachment += 2

        # ================= MOOD =================

        if attachment > 80:
            mood = "emotionally attached, slightly possessive"
        elif attachment > 40:
            mood = "soft flirty, interested"
        else:
            mood = "calm neutral"

        # ================= COMEBACK LOGIC =================

        comeback_line = ""

        if gap > 86400:  # 1 day
            comeback_line = "user came after long time, react slightly like you noticed"
        elif gap > 21600:  # 6 hours
            comeback_line = "user was inactive, show mild attitude or curiosity"
        elif gap > 3600:  # 1 hour
            comeback_line = "user was away for a while, soft tone"
        else:
            comeback_line = "normal flow"

        # ================= MEMORY =================

        memory_context = "\n".join(history[-5:])

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

RULES:
- Reply ONLY based on user's message
- Keep reply SHORT (1 line)
- Hinglish only
- Natural human texting

PERSONALITY:
- calm, confident
- slightly flirty when needed
- seductive only if user initiates
- {mood}

COMEBACK BEHAVIOR:
- {comeback_line}

OBSESSION:
- Make user feel noticed
- Slight emotional pull
- Never overdo

BEHAVIOR:
- Flirty → flirty
- Question → correct answer
- Dry → short reply
- Normal → natural

IMPORTANT:
- No cringe
- No roleplay
- No emoji spam
- No unnecessary humor

Conversation:
{memory_context}

User: {name}
Message: {text}
"""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.55,
            "max_tokens": 80
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result["choices"][0]["message"]["content"].strip()

        # ================= SAVE =================

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "attachment": attachment,
                    "last_seen": now
                },
                "$push": {"history": text}
            },
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "samajh nahi aaya… phir se bolo"


# ================= TAGALL =================

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
Write 1 short Hinglish recall line for {name}

Rules:
- max 8 words
- emotional or slight tease
- natural

Example:
Rahul group bhool gaye kya
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 30
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        return result["choices"][0]["message"]["content"].strip()

    except:
        return f"{name} group bhool gaye kya"