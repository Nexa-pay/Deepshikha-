import os
import uuid
import re
import requests
from gtts import gTTS

from config import (
    ELEVENLABS_API_KEY,
    VOICE_ID,
    VOICE_MODEL,
    VOICE_STYLE
)


# ================= CLEAN TEXT =================

def clean_text(text):
    text = re.sub(r"[^\w\s,.?!]", "", text)

    if len(text) > 250:
        text = text[:250]

    return text.strip()


# ================= STYLE =================

def apply_style(text):
    if VOICE_STYLE == "soft":
        text = text.replace(".", "...").replace("?", "?~")
        return f"{text}"
    return text


# ================= ELEVENLABS =================

def elevenlabs_tts(text, filename):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": VOICE_MODEL,
            "voice_settings": {
                "stability": 0.25,
                "similarity_boost": 0.9,
                "style": 0.85,
                "use_speaker_boost": True
            }
        }

        res = requests.post(url, json=data, headers=headers)

        if res.status_code == 200:
            with open(filename, "wb") as f:
                f.write(res.content)
            return True

        return False

    except Exception as e:
        print("ElevenLabs error:", e)
        return False


# ================= GTTS FALLBACK =================

def gtts_tts(text, filename):
    try:
        tts = gTTS(
            text=text,
            lang="en",  # Hinglish best
            slow=False
        )
        tts.save(filename)
        return True
    except Exception as e:
        print("gTTS error:", e)
        return False


# ================= MAIN FUNCTION =================

def text_to_voice(text, user_id):
    try:
        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        text = clean_text(text)
        text = apply_style(text)

        # 🔥 Try ElevenLabs first
        if ELEVENLABS_API_KEY and VOICE_ID:
            success = elevenlabs_tts(text, filename)
            if success:
                return filename

        # 🔥 fallback to gTTS
        if gtts_tts(text, filename):
            return filename

        return None

    except Exception as e:
        print("Voice error:", e)
        return None


# ================= CLEANUP =================

def delete_voice(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print("Delete error:", e)