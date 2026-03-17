import openai
from database import chats, users
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


def get_memory(user_id):
    user = users.find_one({"user_id": user_id}) or {}
    return user.get("memory", "")


def build_prompt(user_id):
    memory = get_memory(user_id)

    return f"""
You are a charming AI girlfriend.
Memory: {memory}

Style: playful, flirty, caring.
Reply in ONE short sentence only.
"""


def get_history(user_id):
    data = chats.find({"user_id": user_id}).sort("_id", -1).limit(5)

    messages = []
    for d in reversed(list(data)):
        role = "assistant" if d.get("bot") else "user"
        messages.append({"role": role, "content": d["message"]})

    return messages


async def generate_reply(user_id, text):
    messages = [{"role": "system", "content": build_prompt(user_id)}]
    messages += get_history(user_id)
    messages.append({"role": "user", "content": text[:200]})

    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=30
    )

    reply = res["choices"][0]["message"]["content"]

    chats.insert_one({"user_id": user_id, "message": text})
    chats.insert_one({"user_id": user_id, "message": reply, "bot": True})

    return reply
