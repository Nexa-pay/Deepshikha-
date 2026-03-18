import os

# ================= SAFE ENV GET =================

def get_env(key, default=None, cast=str):
    value = os.getenv(key)

    if value is None:
        return default

    try:
        return cast(value)
    except:
        return default


# 🔥 BOOLEAN PARSER (FIX)
def get_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ["true", "1", "yes", "on"]


# ================= CORE =================

OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
BOT_TOKEN = get_env("BOT_TOKEN")
MONGO_URI = get_env("MONGO_URI")
ELEVENLABS_API_KEY = get_env("ELEVENLABS_API_KEY")  # optional

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

CREATIVITY_MODE = get_env("CREATIVITY_MODE", "balanced")


# ================= HUMAN BEHAVIOR =================

MIN_DELAY = get_env("MIN_DELAY", 2, int)
MAX_DELAY = get_env("MAX_DELAY", 6, int)

TYPING_PROBABILITY = get_env("TYPING_PROBABILITY", 100, int)


# ================= AUTO SYSTEM =================

AUTO_MESSAGE_INTERVAL = get_env("AUTO_MESSAGE_INTERVAL", 1800, int)
AUTO_MESSAGE_CHANCE = get_env("AUTO_MESSAGE_CHANCE", 10, int)  # 🔥 NEW


# ================= EMOTIONAL CONTROL =================

JEALOUSY_CHANCE = get_env("JEALOUSY_CHANCE", 12, int)
RANDOM_MESSAGE_CHANCE = get_env("RANDOM_MESSAGE_CHANCE", 8, int)
ATTACHMENT_GAIN = get_env("ATTACHMENT_GAIN", 2, int)

POSSESSIVE_THRESHOLD = get_env("POSSESSIVE_THRESHOLD", 80, int)
LOVE_THRESHOLD = get_env("LOVE_THRESHOLD", 120, int)


# ================= MEDIA CONTROL =================

PHOTO_CHANCE = get_env("PHOTO_CHANCE", 50, int)
STICKER_CHANCE = get_env("STICKER_CHANCE", 6, int)


# ================= VOICE CONFIG =================

VOICE_ID = get_env("VOICE_ID", "Rachel")
VOICE_MODEL = get_env("VOICE_MODEL", "eleven_multilingual_v2")

VOICE_STYLE = get_env("VOICE_STYLE", "soft")  # soft / normal


# ================= FEATURE TOGGLES =================

ENABLE_VOICE = get_bool("ENABLE_VOICE", True)
ENABLE_STICKERS = get_bool("ENABLE_STICKERS", True)
ENABLE_IMAGES = get_bool("ENABLE_IMAGES", True)


# ================= DEBUG =================

DEBUG = get_bool("DEBUG", False)

if DEBUG:
    print("⚙️ DEBUG MODE ENABLED")


# ================= STARTUP LOG =================

print("✅ Config Loaded")