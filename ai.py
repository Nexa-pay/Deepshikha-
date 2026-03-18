import os
import aiohttp
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        history = user_data.get("history", [])

        # 💘 emotional level
        if attachment > 60:
            mood = "slightly attached, deeper tone"
        elif attachment > 30:
            mood = "soft + mildly flirty"
        else:
            mood = "neutral calm"

        # 🧠 last messages memory
        context_memory = "\n".join(history[-3:])

        system_prompt = f"""
You are a real girl chatting on Telegram.

RULES:
- Reply based ONLY on user's message
- No unnecessary jokes
- No over-funny tone
- No random teasing
- Keep reply SHORT (1 line)
- Hinglish only
- Natural human texting

PERSONALITY:
- calm, confident
- slightly flirty when needed 😏
- not childish
- not over expressive
- {mood}

BEHAVIOR:
- If user is normal → normal reply
- If user is flirty → flirty reply
- If user is serious → serious answer
- If user asks fact → give correct answer (no jokes)
- If user is dry → short reply

IMPORTANT:
- No unnecessary emojis
- No forced humor
- No roleplay (*grinning*, etc)
- Respond like real girl, not entertainer

Conversation memory:
{context_memory}

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
            "temperature": 0.5,
            "max_tokens": 80
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result["choices"][0]["message"]["content"].strip()

        # 💘 increase attachment
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 2}},
            upsert=True
        )

        # 🧠 save history
        users.update_one(
            {"user_id": user_id},
            {"$push": {"history": text}},
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "samajh nahi aaya… phir se bolo"


# ================= TAGALL AI =================

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
You are a girl trying to revive a Telegram group.

Write ONE short message for {name}

Rules:
- Hinglish
- 1 line only
- max 8-10 words
- calm + slight tease
- no jokes
- no emojis spam

Examples:
Rahul group bhool gaye kya  
Aman itne busy ho aajkal  
Rohit kabhi yaad bhi karte ho  
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 30
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("TAG ERROR:", e)
        return f"{name} group bhool gaye kya"