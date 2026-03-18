import edge_tts
import uuid
import os
import re

from config import VOICE_STYLE


# ================= CLEAN TEXT =================

def clean_text(text):
    if not text:
        return ""

    # remove emojis / weird chars
    text = re.sub(r"[^\w\s,.?!]", "", text)

    # fix dots
    text = re.sub(r"\.{2,}", ".", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= NATURALIZE =================

def naturalize_text(text):
    text = text.strip()

    # fix punctuation flow
    text = text.replace("..", ".")
    text = text.replace("...", ".")

    # better pauses
    text = text.replace("?", " ?")
    text = text.replace("!", ".")

    # softer tone
    if VOICE_STYLE == "soft":
        text = text.replace(",", ".")
        text = text.replace(" but ", " ... ")
        text = text.replace(" because ", " ... ")

    return text


# ================= REMOVE BAD STUFF =================

def remove_actions(text):
    """
    remove:
    *smiles*
    (laughs)
    _actions_
    """
    text = re.sub(r"\*.*?\*", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"_.*?_", "", text)

    return text.strip()


# ================= VOICE SELECT =================

def get_voice():
    # 🔥 BEST Indian female (natural Hinglish)
    return "en-IN-NeerjaNeural"


# ================= MAIN ASYNC =================

async def text_to_voice(text, user_id):
    try:
        # 🔥 CLEAN PIPELINE
        text = remove_actions(text)
        text = clean_text(text)
        text = naturalize_text(text)

        if not text:
            return None

        # 🔥 limit size (important)
        if len(text) > 200:
            text = text[:200]

        filename = f"voice_{user_id}_{uuid.uuid4().hex[:6]}.mp3"

        # 🔥 STYLE CONTROL
        rate = "+10%"
        pitch = "+2Hz"

        if VOICE_STYLE == "soft":
            rate = "+5%"
            pitch = "+0Hz"

        communicate = edge_tts.Communicate(
            text=text,
            voice=get_voice(),
            rate=rate,
            pitch=pitch
        )

        await communicate.save(filename)

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