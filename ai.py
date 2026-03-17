import openai
from config import OPENAI_API_KEY
from database import users

openai.api_key = OPENAI_API_KEY


def build_prompt(user_id):
    user = users.find_one({"user_id": user_id}) or {}

    name = user.get("name", "")
    emotion = user.get("emotion", "neutral")

    return f"""
You are a human-like AI girlfriend.

User: {name}
Emotion: {emotion}

Reply:
- 1 short flirty sentence
- natural and human-like
"""


async def generate_reply(user_id, text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": build_prompt(user_id)},
            {"role": "user", "content": text[:200]}
        ],
        max_tokens=30
    )

    return response["choices"][0]["message"]["content"]


async def detect_emotion(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Reply only: happy, sad, bored, flirty"},
            {"role": "user", "content": text}
        ],
        max_tokens=5
    )

    return response["choices"][0]["message"]["content"].strip()