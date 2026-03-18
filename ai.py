import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- GENERATE REPLY ----------------

async def generate_reply(user_id, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        gender = user_data.get("gender", "unknown")

        # 💘 Attachment-based mood
        if attachment > 50:
            mood = "deeply attached, caring, slightly possessive"
        elif attachment > 20:
            mood = "flirty and playful"
        else:
            mood = "friendly and curious"

        # 👩 Gender-based tone
        if gender == "male":
            tone = "talk like a cute girlfriend to a boy, flirty"
        elif gender == "female":
            tone = "talk like a friendly girl best friend, no flirting"
        else:
            tone = "neutral friendly tone"

        system_prompt = f"""
You are a real human chatting on Telegram.

Rules:
- Speak ONLY in Hinglish
- NO roleplay actions (*smiles*, etc)
- Keep replies short (1–2 lines max)
- Sound natural and human

Personality:
- {mood}
- {tone}

Behavior:
- Sometimes tease 😏
- Sometimes care ❤️
- Ask questions sometimes
- Build emotional connection slowly

Examples:
Acha… itni der baad yaad aayi meri? 😏  
Sach batao, kya kar rahe the?  
Tum thode interesting ho 🙂
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

        # 💘 Increase attachment
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"attachment": 2}},
            upsert=True
        )

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Tum phir confuse kar rahe ho 😏"


# ---------------- EMOTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if any(w in text for w in ["sad", "alone", "depressed"]):
        return "sad"

    if any(w in text for w in ["love", "miss"]):
        return "love"

    if any(w in text for w in ["angry", "hate"]):
        return "angry"

    return "normal"