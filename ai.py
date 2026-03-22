import aiohttp
import re
from config import TOGETHER_API_KEY, HF_API_KEY, MODEL, HF_MODEL, TEMPERATURE, MAX_TOKENS

TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

print("AI CALLED")

# ================= CLEAN =================
def clean_reply(reply):
    reply = re.sub(r"\*.*?\*", "", reply)
    reply = re.sub(r"\(.*?\)", "", reply)
    reply = re.sub(r"\s+", " ", reply).strip()
    return reply


# ================= TOGETHER =================
async def call_together(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOGETHER_URL,
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "Reply in Hinglish, max 8 words."},
                    {"role": "user", "content": text}
                ],
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS
            }
        ) as res:

            if res.status != 200:
                return None

            data = await res.json()

    return data["choices"][0]["message"]["content"]


# ================= HUGGINGFACE =================
async def call_hf(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HF_URL,
            headers={
                "Authorization": f"Bearer {HF_API_KEY}"
            },
            json={
                "inputs": f"Reply short Hinglish: {text}",
                "parameters": {
                    "max_new_tokens": 50
                }
            }
        ) as res:

            if res.status != 200:
                return None

            data = await res.json()

    if isinstance(data, list):
        return data[0].get("generated_text", "")

    return None


# ================= MAIN =================
async def generate_reply(user_id, name, text):
    try:
        # 1️⃣ Try Together
        reply = await call_together(text)

        if reply:
            print("✅ Using Together")
        else:
            print("⚠️ Together failed, using HF")
            reply = await call_hf(text)

        if not reply:
            return "server busy hai 😌"

        reply = clean_reply(reply)
        reply = " ".join(reply.split()[:8])

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "error aa gaya 😌"