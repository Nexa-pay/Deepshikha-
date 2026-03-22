import aiohttp
import re
from config import OPENROUTER_API_KEY, MODEL, TEMPERATURE, MAX_TOKENS

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= IMAGE =================
IMAGE_URLS = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]

def should_send_image(text):
    return any(x in text.lower() for x in ["photo", "pic", "selfie", "image"])

def get_random_image():
    import random
    return random.choice(IMAGE_URLS)


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

RULES:
- Always reply in Hinglish
- Max 8 words only
- One line reply only
- No explanation
- No roleplay (*)
- Sound natural

IMPORTANT:
- If user asks question → answer correctly
- If normal chat → slightly flirty
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
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
                    return "server busy hai… phir try karo 😌"

                data = await res.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            return "samajh nahi aaya 😌"

        reply = clean_reply(reply)

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "error aa gaya 😌"