from gtts import gTTS
import os
import time
import uuid

# ================= TEXT → VOICE =================

def text_to_voice(text, user_id):
    try:
        # 🔥 unique filename (no overwrite)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"voice_{user_id}_{unique_id}.mp3"

        # 🔥 text trim (avoid long crash)
        if len(text) > 200:
            text = text[:200]

        # 🔥 Hinglish friendly
        tts = gTTS(
            text=text,
            lang='en',      # Hinglish best works with en
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
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print("Delete error:", e)