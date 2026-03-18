import edge_tts
import uuid
import os
import re
import asyncio

from config import VOICE_STYLE


# ================= CLEAN TEXT =================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"[^\w\s,.?!]", "", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= NATURALIZE =================

def naturalize_text(text):
    text = text.strip()

    # remove robotic patterns
    text = text.replace("..", ".")
    text = text.replace("...", ".")

    # natural pauses
    text = text.replace("?", " ?")
    text = text.replace("!", ".")

    if VOICE_STYLE == "soft":
        text = text.replace(",", ".")

    return text


# ================= VOICE SELECT =================

def get_voice():
    # 🔥 Hinglish + Hindi best combo
    return "en-IN-NeerjaNeural"


# ================= ASYNC CORE =================

async def text_to_voice_async(text, user_id):
    try:
        text = clean_text(text)
        text = naturalize_text(text)

        if len(text) > 250:
            text = text[:250]

        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        communicate = edge_tts.Communicate(
            text=text,
            voice=get_voice(),
            rate="+8%",     # 🔥 speed natural
            pitch="+2Hz"    # 🔥 soft female tone
        )

        await communicate.save(filename)

        return filename

    except Exception as e:
        print("Voice error:", e)
        return None


# ================= SYNC WRAPPER =================

def text_to_voice(text, user_id):
    try:
        return asyncio.run(text_to_voice_async(text, user_id))
    except RuntimeError:
        # fallback if loop already running
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(text_to_voice_async(text, user_id))


# ================= DELETE =================

def delete_voice(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print("Delete error:", e)