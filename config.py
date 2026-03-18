import os

# ================= SAFE ENV GET =================

def get_env(key, default=None, cast=str):
    value = os.getenv(key, default)
    try:
        return cast(value)
    except:
        return default


# ================= CORE =================

OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
BOT_TOKEN = get_env("BOT_TOKEN")
MONGO_URI = get_env("MONGO_URI")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY missing")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")


# ================= OWNER =================

OWNER_ID = get_env("OWNER_ID", 123456789, int)


# ================= AI CONFIG =================

MODEL = get_env("MODEL", "deepseek/deepseek-chat")

TEMPERATURE = get_env("TEMPERATURE", 0.75, float)
MAX_TOKENS = get_env("MAX_TOKENS", 80, int)

# reply creativity control
CREATIVITY_MODE = get_env("CREATIVITY_MODE", "balanced")  
# options: low / balanced / high


# ================= HUMAN BEHAVIOR =================

MIN_DELAY = get_env("MIN_DELAY", 2, int)
MAX_DELAY = get_env("MAX_DELAY", 6, int)

TYPING_PROBABILITY = get_env("TYPING_PROBABILITY", 100, int)


# ================= AUTO SYSTEM =================

AUTO_MESSAGE_INTERVAL = get_env("AUTO_MESSAGE_INTERVAL", 1800, int)


# ================= EMOTIONAL CONTROL =================

JEALOUSY_CHANCE = get_env("JEALOUSY_CHANCE", 12, int)
RANDOM_MESSAGE_CHANCE = get_env("RANDOM_MESSAGE_CHANCE", 8, int)
ATTACHMENT_GAIN = get_env("ATTACHMENT_GAIN", 2, int)

# 🔥 new controls
POSSESSIVE_THRESHOLD = get_env("POSSESSIVE_THRESHOLD", 80, int)
LOVE_THRESHOLD = get_env("LOVE_THRESHOLD", 120, int)


# ================= MEDIA CONTROL =================

PHOTO_CHANCE = get_env("PHOTO_CHANCE", 50, int)
STICKER_CHANCE = get_env("STICKER_CHANCE", 6, int)


# ================= FEATURE TOGGLES =================

ENABLE_VOICE = get_env("ENABLE_VOICE", "False").lower() == "true"
ENABLE_STICKERS = get_env("ENABLE_STICKERS", "True").lower() == "true"
ENABLE_IMAGES = get_env("ENABLE_IMAGES", "True").lower() == "true"


# ================= DEBUG =================

DEBUG = get_env("DEBUG", "False").lower() == "true"

if DEBUG:
    print("⚙️ DEBUG MODE ENABLED")