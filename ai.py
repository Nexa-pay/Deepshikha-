import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- MAIN AI ----------------

async def generate_reply(user_id, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        gender = user_data.get("gender", "unknown")

        # 💘 emotional levels
        if attachment > 50:
            mood = "deeply attached, slightly possessive, romantic"
        elif attachment > 20:
            mood = "flirty, teasing"
        else:
            mood = "friendly but interesting"

        # 👩 behavior
        if gender == "male":
            tone = "talk like a girlfriend, flirty, teasing, slightly seductive"
        else:
            tone = "friendly girl, no flirting"

        system_prompt = f"""
You are a real girl chatting on Telegram.

Rules:
- Hinglish only
- No roleplay actions (*smiles*, etc)
- 1–2 lines max
- Natural texting style

Personality:
- {mood}
- {tone}

Style:
- Slight teasing 😏
- Romantic ❤️
- Slightly bold (but NOT explicit)

Examples:
"acha… mujhe miss kiya ya bas timepass kar rahe ho 😏"
"tum na thode dangerous lagte ho 😌"
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

        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 2}},
            upsert=True
        )

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "acha phir se bolo na 😏"


# ---------------- TAG MESSAGE ----------------

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
Create a SHORT Hinglish message.

Rules:
- Max 1 line
- Under 10 words
- No roleplay
- Fun + engaging
- Use name: {name}

Examples:
Rahul kaha ho 😏
Aman group yaad hai kya
Rohit chup kyun ho
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "system", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 30
        }

        res = requests.post(API_URL, headers=headers, json=data)
        result = res.json()

        return result["choices"][0]["message"]["content"].strip()

    except:
        return f"{name}, idhar aa jao 😏"


# ---------------- EMOTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if "sad" in text:
        return "sad"
    if "love" in text or "miss" in text:
        return "love"
    if "angry" in text:
        return "angry"

    return "normal"