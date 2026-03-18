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
    if not text:
        return ""

    # remove emojis & symbols
    text = re.sub(r"[^\w\s,.?!]", "", text)

    # remove multiple dots
    text = re.sub(r"\.{2,}", ".", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= HINGLISH NATURALIZER =================

def naturalize_text(text):
    text = text.strip()

    # 🔥 remove robotic endings
    text = text.replace("..", ".")
    text = text.replace("...", ".")

    # 🔥 soft conversational tweaks
    text = text.replace("?", " ?")
    text = text.replace("!", ".")

    # 🔥 small pause (natural)
    if VOICE_STYLE == "soft":
        text = text.replace(",", ".")

    return text


# ================= MAIN VOICE =================

def text_to_voice(text, user_id):
    try:
        if not ELEVENLABS_API_KEY:
            return None

        # 🔥 CLEAN FLOW
        text = clean_text(text)
        text = naturalize_text(text)

        # 🔥 limit size (important)
        if len(text) > 250:
            text = text[:250]

        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": VOICE_MODEL,

            # 🔥 PERFECT BALANCE (tested)
            "voice_settings": {
                "stability": 0.28,          # 🔥 less robotic
                "similarity_boost": 0.9,
                "style": 0.65,              # 🔥 natural emotion
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