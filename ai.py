import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}


def build_prompt(user_id, text):
    user = users.find_one({"user_id": user_id}) or {}

    name = user.get("name", "")
    emotion = user.get("emotion", "neutral")

    return f"""
You are a flirty AI girlfriend.

User: {name}
Emotion: {emotion}

Reply in:
- 1 short sentence
- human-like
- slightly flirty

User: {text}
"""


async def generate_reply(user_id, text):
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a flirty AI girlfriend."},
            {"role": "user", "content": build_prompt(user_id, text)}
        ],
        "max_tokens": 40
    }

    res = requests.post(API_URL, headers=headers, json=payload)

    try:
        return res.json()["choices"][0]["message"]["content"]
    except:
        return "Hmm… say that again 😌"


async def detect_emotion(text):
    text = text.lower()

    if any(x in text for x in ["sad", "hurt", "cry"]):
        return "sad"
    if any(x in text for x in ["love", "miss", "baby"]):
        return "flirty"
    if any(x in text for x in ["bored", "meh"]):
        return "bored"

    return "happy"