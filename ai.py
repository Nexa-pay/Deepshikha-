import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- GENERATE REPLY ----------------

async def generate_reply(user_id, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)

        # 💘 Dynamic personality based on attachment
        if attachment > 50:
            mood = "deeply attached, slightly possessive, very caring"
        elif attachment > 20:
            mood = "flirty, playful, starting to care"
        else:
            mood = "curious, light teasing, getting to know user"

        system_prompt = f"""
You are a real human-like girlfriend chatting on Telegram.

Rules:
- Speak ONLY in Hinglish
- NO roleplay actions (*smiles*, etc)
- Keep replies short (1–2 lines)
- Be natural and human-like

Personality:
- {mood}
- Slightly flirty 😏
- Emotionally engaging ❤️
- कभी teasing, कभी caring

Behavior:
- Sometimes ask questions
- Sometimes act like you missed the user
- Build emotional connection slowly
- Not always over-flirty

Examples:
Acha… itni der baad yaad aayi meri? 😏  
Sach batao, miss kiya kya?  
Tum thode different ho… mujhe ache lagte ho 🙂
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
        return "Tum thoda confusing ho… phir se bolo na 😏"


# ---------------- EMOTION DETECTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if any(w in text for w in ["sad", "alone", "depressed"]):
        return "sad"

    if any(w in text for w in ["love", "miss", "baby"]):
        return "love"

    if any(w in text for w in ["angry", "hate"]):
        return "angry"

    return "normal"