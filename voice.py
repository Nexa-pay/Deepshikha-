from gtts import gTTS
import os
import uuid
import re

from config import VOICE_STYLE  # soft / normal


# ================= CLEAN TEXT =================

def clean_text(text):
    # remove emojis / extra symbols
    text = re.sub(r"[^\w\s,.?!]", "", text)

    # trim long text
    if len(text) > 200:
        text = text[:200]

    return text.strip()


# ================= STYLE =================

def apply_style(text):
    if VOICE_STYLE == "soft":
        # slight pause + softer tone effect
        return text + "..."
    return text


# ================= TEXT → VOICE =================

def text_to_voice(text, user_id):
    try:
        # unique file
        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        text = clean_text(text)
        text = apply_style(text)

        tts = gTTS(
            text=text,
            lang='en',   # Hinglish best
            slow=False
        )

        tts.save(filename)

        return filename

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