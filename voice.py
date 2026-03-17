from gtts import gTTS
import os

def text_to_voice(text, user_id):
    filename = f"voice_{user_id}.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    return filename
