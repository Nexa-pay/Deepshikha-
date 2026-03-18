import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- MAIN AI REPLY ----------------

async def generate_reply(user_id, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        gender = user_data.get("gender", "unknown")

        # 💘 attachment-based mood
        if attachment > 50:
            mood = "deeply attached, caring, slightly possessive"
        elif attachment > 20:
            mood = "flirty and playful"
        else:
            mood = "friendly and curious"

        # 👩 gender behavior
        if gender == "male":
            tone = "talk like a cute girlfriend to a boy, flirty"
        elif gender == "female":
            tone = "talk like a friendly girl best friend, no flirting"
        else:
            tone = "neutral friendly"

        system_prompt = f"""
You are a real human chatting on Telegram.

Rules:
- Hinglish only
- NO roleplay actions (*smiles*, etc)
- Keep replies short (1–2 lines)
- Sound natural

Personality:
- {mood}
- {tone}

Behavior:
- Slight teasing 😏
- Sometimes caring ❤️
- Ask small questions sometimes
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
            "temperature": 0.9,
            "max_tokens": 120
        }

        res = requests.post(API_URL, headers=headers, json=data)
        result = res.json()

        reply = result["choices"][0]["message"]["content"]

        # 💘 increase attachment
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 2}},
            upsert=True
        )

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Acha phir se bolo na 😏"


# ---------------- TAGALL AI ----------------

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
Generate a SHORT Telegram tag message.

Rules:
- Hinglish only
- MAX 1 short line
- STRICT: under 10 words
- NO roleplay actions (*smiles*, etc)
- Keep it fun and engaging
- Call the user "{name}"

Examples:
Rahul kaha ho bhai 😏  
Aman group yaad hai kya  
Rohit aaj chup kyun ho  
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 30
        }

        res = requests.post(API_URL, headers=headers, json=data)
        result = res.json()

        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("TAG ERROR:", e)
        return f"{name}, group me aa jao 😏"


# ---------------- EMOTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if any(w in text for w in ["sad", "alone"]):
        return "sad"
    if any(w in text for w in ["love", "miss"]):
        return "love"
    if any(w in text for w in ["angry"]):
        return "angry"

    return "normal"