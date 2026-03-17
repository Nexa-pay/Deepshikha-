import openai
from config import OPENAI_API_KEY
from database import users, chats

openai.api_key = OPENAI_API_KEY


def build_prompt(user_id):
    user = users.find_one({"user_id": user_id}) or {}

    name = user.get("name", "")
    emotion = user.get("emotion", "neutral")
    stage = user.get("relationship_stage", 1)
    memory = user.get("memory", "")

    return f"""
You are a human-like AI girlfriend.

User: {name}
Emotion: {emotion}
Stage: {stage}
Memory: {memory}

Reply rules:
- 1 short sentence
- natural, human-like
- slightly flirty
- emotionally aware
"""


async def generate_reply(user_id, text):
    messages = [
        {"role": "system", "content": build_prompt(user_id)},
        {"role": "user", "content": text[:200]}
    ]

    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=30
    )

    reply = res["choices"][0]["message"]["content"]

    chats.insert_one({"user_id": user_id, "message": text})
    chats.insert_one({"user_id": user_id, "message": reply, "bot": True})

    return reply


async def detect_emotion(text):
    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return emotion: happy, sad, bored, flirty"},
            {"role": "user", "content": text}
        ],
        max_tokens=5
    )

    return res["choices"][0]["message"]["content"].strip()