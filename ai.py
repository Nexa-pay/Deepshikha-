import aiohttp
import time
from config import OPENROUTER_API_KEY
from database import users

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= MESSAGE TYPE =================

def detect_type(text):
    text = text.lower()

    if any(x in text for x in ["love", "miss", "baby", "jaan"]):
        return "flirty"
    elif any(x in text for x in ["why", "what", "who", "kaise", "kya"]):
        return "question"
    elif len(text.split()) <= 2:
        return "dry"
    else:
        return "normal"


# ================= PERSONALITY =================

def analyze_user(text):
    text = text.lower()

    personality = "normal"
    topics = []

    if any(x in text for x in ["love", "miss", "baby", "jaan"]):
        personality = "flirty"
        topics.append("love")

    elif any(x in text for x in ["sad", "alone", "hurt"]):
        personality = "emotional"
        topics.append("emotions")

    elif any(x in text for x in ["money", "earn", "business"]):
        topics.append("money")

    elif len(text.split()) <= 2:
        personality = "dry"

    return personality, topics


# ================= TIME GAP =================

def get_gap(last_time):
    try:
        if not last_time:
            return 0
        if isinstance(last_time, str):
            last_time = int(last_time)
        return int(time.time()) - last_time
    except:
        return 0


# ================= MAIN AI =================

async def generate_reply(user_id, name, text):
    try:
        user_data = users.find_one({"user_id": user_id}) or {}

        attachment = user_data.get("attachment", 0)
        relationship = user_data.get("relationship", 0)
        ignore_count = user_data.get("ignore_count", 0)

        history = user_data.get("history", [])
        last_seen = user_data.get("last_seen")

        personality_data = user_data.get("personality", {})
        fav_data = user_data.get("favorites", {})

        now = int(time.time())
        gap = get_gap(last_seen)

        msg_type = detect_type(text)
        personality, topics = analyze_user(text)

        # ================= RELATIONSHIP SYSTEM =================

        if msg_type == "flirty":
            attachment += 5
            relationship += 5
        elif msg_type == "dry":
            attachment += 1
            relationship += 1
            ignore_count += 1
        else:
            attachment += 2
            relationship += 2

        # ================= MOOD =================

        if relationship > 100:
            mood = "emotionally attached, slightly possessive"
        elif relationship > 50:
            mood = "soft flirty, interested"
        else:
            mood = "calm neutral"

        # ================= COMEBACK =================

        if gap > 86400:
            comeback = "user came after long time, react like you noticed"
        elif gap > 21600:
            comeback = "user was inactive, slight attitude"
        elif gap > 3600:
            comeback = "user was away, soft tone"
        else:
            comeback = "normal flow"

        # ================= POSSESSIVE TRIGGER =================

        possessive_hint = ""

        if relationship > 80 and msg_type == "flirty":
            possessive_hint = "add slight possessive teasing tone"
        elif ignore_count > 5:
            possessive_hint = "show mild attitude, feels ignored"

        # ================= MEMORY =================

        memory_context = "\n".join(history[-10:])
        user_type = personality_data.get("type", "normal")
        fav_topics = ", ".join(fav_data.get("topics", []))

        # ================= PROMPT =================

        system_prompt = f"""
You are a real girl chatting on Telegram.

RULES:
- Reply ONLY based on user's message
- Continue conversation naturally
- Keep reply SHORT (1 line)
- Hinglish only

PERSONALITY:
- calm, confident
- slightly flirty when needed
- seductive only if user initiates
- {mood}

USER PROFILE:
- Personality: {user_type}
- Favorite topics: {fav_topics}

EMOTIONAL MEMORY:
- You remember past chats
- If user ignores → slight attitude
- If user returns → react like you noticed
- If user is consistent → feel closer

COMEBACK:
- {comeback}

POSSESSIVE:
- {possessive_hint}

IMPORTANT:
- No cringe
- No roleplay
- No emoji spam
- No unnecessary humor

Conversation History (very important, continue naturally):
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
            "temperature": 0.55,
            "max_tokens": 80
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as res:
                result = await res.json()

        reply = result.get("choices", [{}])[0].get("message", {}).get("content")

        if not reply:
            return "samajh nahi aaya… phir bolo"

        reply = reply.strip()

        # ================= SAVE =================

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "attachment": attachment,
                    "relationship": relationship,
                    "ignore_count": ignore_count,
                    "last_seen": now,
                    "personality.type": personality
                },
                "$addToSet": {
                    "favorites.topics": {"$each": topics}
                },
                "$push": {
                    "history": {
                        "$each": [
                            f"User: {text}",
                            f"Bot: {reply}"
                        ],
                        "$slice": -15
                    }
                }
            },
            upsert=True
        )

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "clear nahi hua… phir bolo"


# ================= TAGALL =================

async def generate_tag_message(name):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = f"""
Write 1 short Hinglish recall line for {name}

Rules:
- max 8 words
- emotional or slight tease
- natural
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

        return result.get("choices", [{}])[0].get("message", {}).get("content", f"{name} kaha ho").strip()

    except:
        return f"{name} group bhool gaye kya"