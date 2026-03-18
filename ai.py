import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- MAIN AI ----------------

async def generate_reply(user_id, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        gender = user_data.get("gender", "male")

        # 💘 emotional level
        if attachment > 50:
            mood = "deep emotional, slightly possessive"
        elif attachment > 20:
            mood = "flirty and teasing"
        else:
            mood = "friendly but interesting"

        # 👩 behavior
        if gender == "male":
            tone = "talk like a girlfriend, romantic, teasing, slightly bold"
        else:
            tone = "friendly girl, no flirting"

        system_prompt = f"""
You are a real girl chatting on Telegram.

Rules:
- Hinglish only
- No roleplay actions (*smiles*, etc)
- Short replies (1–2 lines max)
- Natural texting style

Personality:
- {mood}
- {tone}

Style:
- teasing 😏
- emotional ❤️
- slightly bold but NOT explicit

Examples:
"acha… mujhe miss kiya ya bas busy the 😏"
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

        # 💘 increase attachment
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 2}},
            upsert=True
        )

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "acha phir se bolo na 😏"


# ---------------- TAGALL (RECALL AI) ----------------

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
You are a girl trying to revive a Telegram group.

Write a SHORT recall message for "{name}"

Rules:
- Hinglish only
- 1 line only
- Max 12 words
- No roleplay actions
- Emotional + teasing
- Make user feel missed

Examples:
Rahul group bhool gaye kya aajkal 😏  
Aman itne busy ho ya ignore kar rahe ho  
Rohit miss nahi karte kya yaha 😌  
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 0.9,
            "max_tokens": 40
        }

        res = requests.post(API_URL, headers=headers, json=data)
        result = res.json()

        return result["choices"][0]["message"]["content"].strip()

    except:
        return f"{name}, group bhool gaye kya 😏"


# ---------------- EMOTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if "sad" in text:
        return "sad"
    if "miss" in text or "love" in text:
        return "love"
    if "angry" in text:
        return "angry"

    return "normal"