import aiohttp
import re
from config import TOGETHER_API_KEY, MODEL, TEMPERATURE, MAX_TOKENS

API_URL = "https://api.together.xyz/v1/chat/completions"


# ================= CLEAN =================
def clean_reply(reply):
    reply = re.sub(r"\*.*?\*", "", reply)
    reply = re.sub(r"\(.*?\)", "", reply)
    reply = re.sub(r"\s+", " ", reply).strip()
    return reply


# ================= AI =================
async def generate_reply(user_id, name, text):
    try:
        system_prompt = """
You are a real girl chatting on Telegram.

Rules:
- Hinglish only
- Max 8 words
- One line only
- No explanation
- No roleplay

Behavior:
- If question → correct answer
- If normal → slightly flirty
"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                }
            ) as res:

                if res.status != 200:
                    print("API ERROR:", res.status)
                    return "server busy hai 😌"

                data = await res.json()

        reply = data["choices"][0]["message"]["content"]

        reply = clean_reply(reply)

        # limit words
        reply = " ".join(reply.split()[:8])

        return reply or "samajh nahi aaya 😌"

    except Exception as e:
        print("AI ERROR:", e)
        return "error aa gaya 😌"