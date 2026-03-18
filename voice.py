import requests
import uuid
import os
import re

from config import (
    ELEVENLABS_API_KEY,
    VOICE_ID,
    VOICE_MODEL,
    VOICE_STYLE
)

# ================= CLEAN TEXT =================

def clean_text(text):
    text = re.sub(r"[^\w\s,.?!]", "", text)

    if len(text) > 200:
        text = text[:200]

    return text.strip()


# ================= HINGLISH BOOST =================

def style_text(text):
    if VOICE_STYLE == "soft":
        # 🔥 natural pauses
        text = text.replace(",", "...")
        text = text + "..."

    return text


# ================= ELEVEN VOICE =================

def text_to_voice(text, user_id):
    try:
        if not ELEVENLABS_API_KEY:
            return None

        text = clean_text(text)
        text = style_text(text)

        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": VOICE_MODEL,

            # 🔥 MAGIC SETTINGS (REALISTIC)
            "voice_settings": {
                "stability": 0.35,        # 🔥 less robotic
                "similarity_boost": 0.85,
                "style": 0.7,             # 🔥 more expressive
                "use_speaker_boost": True
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            print("Eleven error:", response.text)
            return None

        with open(filename, "wb") as f:
            f.write(response.content)

        return filename

    except Exception as e:
        print("Voice error:", e)
        return None


# ================= DELETE =================

def delete_voice(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print("Delete error:", e)