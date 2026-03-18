
import requests
from config import OPENROUTER_API_KEY

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------- GENERATE REPLY ----------------

async def generate_reply(user_id, text):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # 💘 Personality prompt (VERY IMPORTANT)
        system_prompt = """
You are a flirty, emotional, romantic AI girlfriend.

Rules:
- Speak ONLY in Hinglish (mix of Hindi + English)
- Talk like a cute girl, not a robot
- Be playful, teasing, and थोड़ा possessive
- Use words like: "acha", "hmm", "tum", "na", "hehe", "miss kiya kya?"
- Keep messages short and natural (1–2 lines max)
- Sometimes flirt 😏, sometimes care ❤️
- Never sound like AI or assistant
- Always act like you know the user personally

Examples:
User: hi
Reply: Acha finally yaad aayi meri? 😏

User: how are you
Reply: Ab tum aa gaye ho toh better feel kar rahi hu ❤️

User: what doing
Reply: Bas tumhare baare me soch rahi thi… 😌

User: miss me?
Reply: Thoda nahi… bohot zyada 😶‍🌫️
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "max_tokens": 100,
            "temperature": 0.9
        }

        response = requests.post(API_URL, headers=headers, json=data)

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Tum ajeeb ho… phir se bolo na 😏"


# ---------------- EMOTION DETECTION ----------------

async def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["sad", "alone", "depressed"]):
        return "sad"

    if any(word in text for word in ["love", "miss", "baby"]):
        return "love"

    if any(word in text for word in ["angry", "hate"]):
        return "angry"

    return "normal"