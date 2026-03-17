import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

def get_int_env(key, default=0):
    try:
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return int(value)
    except:
        return default

OWNER_ID = get_int_env("OWNER_ID")
GROUP_ID = get_int_env("GROUP_ID")