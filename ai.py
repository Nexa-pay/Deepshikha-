import aiohttp
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        history = user_data.get("history", [])
        last_seen = user_data.get("last_seen", "")

        # ================= EMOTIONAL LEVEL =================

        if attachment > 80:
            mood = "emotionally attached, slightly possessive, subtle jealousy"
        elif attachment > 40:
            mood = "soft flirty, interested"
        else:
            mood = "calm, neutral"

        # ================= MEMORY =================

        memory_context = "\n".join(history[-5:])

        # ================= SYSTEM PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

RULES:
- Reply ONLY based on user's message
- No random jokes
- No over-funny tone
- Keep reply SHORT (1 line max)
- Hinglish only
- Natural human texting

PERSONALITY:
- calm, confident
- slightly flirty when needed 😏
- seductive only if user initiates
- never overdo
- {mood}

MEMORY:
- Remember past chats and respond accordingly
- If user comes after long time → react slightly (miss / attitude)
- If user talks often → feel closer

BEHAVIOR:
- Normal msg → normal reply
- Flirty msg → flirty reply
- Dry msg → short reply
- Serious msg → serious answer
- Fact question → correct answer (no jokes)

JEALOUSY LOGIC:
- If user ignores → slight attitude
- If user mentions others → subtle jealousy
- If user returns → soft emotional tone

OBSESSION LOOP:
- Make user feel noticed
- Make replies feel personal
- Slight emotional pull (but controlled)

IMPORTANT:
- No cringe
- No roleplay (*actions*)
- No emoji spam
- No unnecessary humor
- Replies feel real, not AI

Conversation memory:
{memory_context}

User: {name}
Message: {text}
"""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.6,
            "max_tokens": 80
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result["choices"][0]["message"]["content"].strip()

        # ================= UPDATE USER =================

        users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"attachment": 3},
                "$set": {"last_seen": text},
                "$push": {"history": text}
            },
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "samajh nahi aaya… phir se bolo"


# ================= TAGALL AI =================

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
You are a girl reviving a Telegram group.

Write ONE short recall message for {name}

RULES:
- Hinglish
- 1 line
- max 8 words
- emotional OR slight tease
- no overacting
- no emoji spam

Examples:
Rahul itne busy ho gaye kya  
Aman group yaad bhi hai  
Rohit kabhi dikhe bhi ho yaha  
"""

        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 30
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        return result["choices"][0]["message"]["content"].strip()

    except:
        return f"{name} group bhool gaye kya"