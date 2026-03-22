import aiohttp
from config import OPENROUTER_API_KEY, MODEL, TEMPERATURE, MAX_TOKENS
from database import get_history

print("✅ AI FILE LOADED")


# ================= BASIC ANSWERS =================

def basic_answer(text):
    t = text.lower()

    if "capital of india" in t:
        return "New Delhi 🙂"

    if "pm of india" in t:
        return "Narendra Modi 😌"

    if "president of india" in t:
        return "Droupadi Murmu 🙂"

    if "captain of india" in t:
        return "Rohit Sharma 🏏"

    return None


# ================= AI CALL =================

async def call_ai(messages):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS
            }
        ) as res:

            if res.status != 200:
                print("❌ API ERROR:", res.status)
                return None

            data = await res.json()
            return data["choices"][0]["message"]["content"]


# ================= MAIN =================

async def generate_reply(user_id, name, text):
    print("🔥 AI CALLED:", text)

    # ✅ 1. Basic answer
    basic = basic_answer(text)
    if basic:
        return basic

    # ✅ 2. Get memory
    history = get_history(user_id)

    messages = [
        {
            "role": "system",
            "content": "Reply short Hinglish, natural, slightly flirty"
        }
    ]

    for h in history[-10:]:
        messages.append({
            "role": h["role"],
            "content": h["text"]
        })

    messages.append({"role": "user", "content": text})

    # ✅ 3. AI call
    reply = await call_ai(messages)

    if not reply:
        return "network slow hai… phir bolo 😌"

    return reply.strip()[:100]