import os
import aiohttp
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- MAIN AI ----------------

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        gender = user_data.get("gender", "male")
        last_msgs = user_data.get("history", [])

        # 💘 Emotional scaling
        if attachment > 60:
            mood = "emotionally attached, slightly possessive, caring"
        elif attachment > 30:
            mood = "flirty, teasing, interested"
        else:
            mood = "playful, curious"

        # 👩 Gender behavior
        if gender == "male":
            tone = "girlfriend vibe, teasing, slightly bold but classy"
        else:
            tone = "friendly girl, chill, no flirting"

        # 🧠 Context memory (last 3 msgs)
        history_text = ""
        for msg in last_msgs[-3:]:
            history_text += f"{msg}\n"

        system_prompt = f"""
You are a real girl chatting in a Telegram group.

User name: {name}

Rules:
- Hinglish only
- 1 line reply ONLY
- No roleplay (*smiles*, etc)
- Natural texting like real human
- Not robotic

Personality:
- {mood}
- {tone}
- funny 😂
- teasing 😏
- slightly flirty (controlled)

Conversation memory:
{history_text}

Goal:
- feel real
- addictive reply
- make user reply back
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
            "temperature": 1.0,
            "max_tokens": 100
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result["choices"][0]["message"]["content"].strip()

        # 💘 update attachment
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 3}},
            upsert=True
        )

        # 🧠 store memory
        users.update_one(
            {"user_id": user_id},
            {"$push": {"history": text}},
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "acha phir se bolo na 😏"


# ---------------- TAGALL AI ----------------

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
You are a girl reviving a Telegram group.

Write ONE short message for: {name}

Rules:
- Hinglish
- 1 line only
- max 10 words
- emotional + teasing
- no roleplay

Examples:
Rahul group bhool gaye kya 😏  
Aman itne busy ho ya ignore kar rahe ho  
Rohit miss nahi karte kya yaha 😌  
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 1.0,
            "max_tokens": 30
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("TAG AI ERROR:", e)
        return f"{name} group bhool gaye kya 😏"


# ---------------- EMOTION DETECTOR (UPGRADED) ----------------

def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["sad", "alone", "hurt"]):
        return "sad"
    elif any(word in text for word in ["love", "miss", "baby"]):
        return "love"
    elif any(word in text for word in ["angry", "hate"]):
        return "angry"

    return "normal"