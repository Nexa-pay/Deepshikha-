import aiohttp
import random

print("✅ AI FILE LOADED")

# ================= BASIC FACTS (NO FAIL SYSTEM) =================

def basic_answer(text):
    t = text.lower()

    if "capital of india" in t:
        return "New Delhi 🙂"

    if "pm of india" in t or "prime minister of india" in t:
        return "Narendra Modi 😌"

    if "president of india" in t:
        return "Droupadi Murmu 🙂"

    if "who are you" in t or "tum kaun ho" in t:
        return "main Deepsikha hu… yaad rakhna 😏"

    return None


# ================= TOGETHER API =================

TOGETHER_API_KEY = "YOUR_TOGETHER_API_KEY"

async def call_together(text):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistralai/Mistral-7B-Instruct-v0.1",
                    "messages": [
                        {"role": "system", "content": "Reply short, Hinglish, natural."},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 60
                }
            ) as res:

                if res.status != 200:
                    return None

                data = await res.json()
                return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("Together error:", e)
        return None


# ================= HUGGINGFACE API =================

HF_API_KEY = "YOUR_HF_API_KEY"

async def call_hf(text):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                json={"inputs": text}
            ) as res:

                if res.status != 200:
                    return None

                data = await res.json()

                if isinstance(data, list):
                    return data[0].get("generated_text", None)

                return None

    except Exception as e:
        print("HF error:", e)
        return None


# ================= MAIN =================

async def generate_reply(user_id, name, text):
    print("🔥 AI CALLED:", text)

    # ✅ 1. Basic answers (instant)
    basic = basic_answer(text)
    if basic:
        return basic

    # ✅ 2. Together API
    reply = await call_together(text)
    if reply:
        return reply[:80]

    print("⚠️ Together failed")

    # ✅ 3. HuggingFace fallback
    reply = await call_hf(text)
    if reply:
        return reply[:80]

    print("⚠️ HF failed")

    # ❌ Final fallback
    return random.choice([
        "server busy… phir try karo 😌",
        "thoda wait karo… fir pucho 😏",
        "abhi slow hai… try again 🙂"
    ])