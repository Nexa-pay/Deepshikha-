import requests
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}


# ------------------ PROMPT ------------------

def build_prompt(user_id, text):
    user = users.find_one({"user_id": user_id}) or {}

    name = user.get("name", "")
    emotion = user.get("emotion", "neutral")
    attachment = user.get("attachment_score", 0)

    mood = "playful"
    if attachment > 50:
        mood = "romantic"
    elif emotion == "sad":
        mood = "caring"

    return f"""
You are a human-like AI girlfriend.

User: {name}
Emotion: {emotion}
Mood: {mood}

Rules:
- reply in 1 short sentence
- natural + flirty
- human tone (not robotic)

User: {text}
AI:
"""


# ------------------ GENERATE REPLY ------------------

async def generate_reply(user_id, text):
    try:
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a flirty AI girlfriend."},
                {"role": "user", "content": build_prompt(user_id, text)}
            ],
            "max_tokens": 40,
            "temperature": 0.9
        }

        res = requests.post(API_URL, headers=headers, json=payload, timeout=15)

        data = res.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Hmm… you went quiet on me 😏"


# ------------------ EMOTION DETECTION ------------------

async def detect_emotion(text):
    text = text.lower()

    if any(x in text for x in ["sad", "hurt", "cry", "alone"]):
        return "sad"

    if any(x in text for x in ["love", "miss", "baby", "kiss"]):
        return "flirty"

    if any(x in text for x in ["bored", "meh", "nothing"]):
        return "bored"

    return "happy"