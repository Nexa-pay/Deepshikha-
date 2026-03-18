import aiohttp
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


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        history = user_data.get("history", [])

        msg_type = detect_type(text)

        # ================= ATTACHMENT LOGIC =================

        if msg_type == "flirty":
            attachment += 5
        elif msg_type == "dry":
            attachment += 1
        else:
            attachment += 2

        # ================= MOOD =================

        if attachment > 80:
            mood = "emotionally attached, slightly possessive, subtle jealousy"
        elif attachment > 40:
            mood = "soft flirty, interested"
        else:
            mood = "calm, neutral"

        # ================= MEMORY =================

        memory_context = "\n".join(history[-5:])

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

RULES:
- Reply ONLY based on user's message
- No unnecessary jokes
- Keep reply SHORT (1 line)
- Hinglish only
- Natural human texting

PERSONALITY:
- calm, confident
- slightly flirty when needed
- seductive only if user initiates
- {mood}

BEHAVIOR:
- Flirty msg → flirty reply
- Question → clear answer
- Dry msg → short reply
- Normal → natural reply

JEALOUSY:
- If ignored → slight attitude
- If user mentions others → subtle jealousy

IMPORTANT:
- No cringe
- No roleplay
- No emoji spam
- No random humor

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
                "$set": {"attachment": attachment},
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