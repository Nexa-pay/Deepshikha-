import os

OWNER_NAME = "Aakash"

# ================= SAFE ENV GET =================

def get_env(key, default=None, cast=str):
    value = os.getenv(key)

    if value is None:
        return default

    try:
        return cast(value)
    except Exception:
        return default


# ================= BOOLEAN PARSER =================

def get_bool(key, default=False):
    value = os.getenv(key)

    if value is None:
        return default

    return str(value).lower() in ["true", "1", "yes", "on"]


# ================= SAFE RANGE =================

def clamp(value, min_v, max_v):
    try:
        return max(min_v, min(max_v, value))
    except Exception:
        return min_v


# ================= CORE =================

OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
BOT_TOKEN = get_env("BOT_TOKEN")
MONGO_URI = get_env("MONGO_URI")

# optional (voice)
ELEVENLABS_API_KEY = get_env("ELEVENLABS_API_KEY", None)


# ================= REQUIRED CHECK =================

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY missing")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")


# ================= OWNER =================

OWNER_ID = get_env("OWNER_ID", 123456789, int)


# ================= AI CONFIG =================

# 🔥 KEEP YOUR MODEL (safe)
MODEL = get_env("MODEL", "deepseek/deepseek-chat")

# 🔥 slightly stable (no big change)
TEMPERATURE = clamp(get_env("TEMPERATURE", 0.7, float), 0.1, 1.5)

# 🔥 small increase (better replies, not too long)
MAX_TOKENS = clamp(get_env("MAX_TOKENS", 70, int), 20, 120)

CREATIVITY_MODE = get_env("CREATIVITY_MODE", "balanced")


# ================= HUMAN BEHAVIOR =================

MIN_DELAY = clamp(get_env("MIN_DELAY", 2, int), 1, 8)
MAX_DELAY = clamp(get_env("MAX_DELAY", 5, int), 2, 10)

TYPING_PROBABILITY = clamp(get_env("TYPING_PROBABILITY", 100, int), 0, 100)


# ================= AUTO SYSTEM =================

AUTO_MESSAGE_INTERVAL = clamp(get_env("AUTO_MESSAGE_INTERVAL", 1800, int), 60, 7200)
AUTO_MESSAGE_CHANCE = clamp(get_env("AUTO_MESSAGE_CHANCE", 10, int), 1, 100)


# ================= EMOTIONAL CONTROL =================

JEALOUSY_CHANCE = clamp(get_env("JEALOUSY_CHANCE", 10, int), 0, 100)
RANDOM_MESSAGE_CHANCE = clamp(get_env("RANDOM_MESSAGE_CHANCE", 5, int), 0, 100)

ATTACHMENT_GAIN = clamp(get_env("ATTACHMENT_GAIN", 2, int), 1, 10)

POSSESSIVE_THRESHOLD = clamp(get_env("POSSESSIVE_THRESHOLD", 80, int), 10, 200)
LOVE_THRESHOLD = clamp(get_env("LOVE_THRESHOLD", 120, int), 20, 300)


# ================= MEDIA CONTROL =================

PHOTO_CHANCE = clamp(get_env("PHOTO_CHANCE", 40, int), 0, 100)
STICKER_CHANCE = clamp(get_env("STICKER_CHANCE", 50, int), 0, 100)


# ================= VOICE CONFIG =================

VOICE_ID = get_env("VOICE_ID", "edge_default")
VOICE_MODEL = get_env("VOICE_MODEL", "edge")
VOICE_STYLE = get_env("VOICE_STYLE", "soft")


# ================= FEATURE TOGGLES =================

ENABLE_VOICE = get_bool("ENABLE_VOICE", True)
ENABLE_STICKERS = get_bool("ENABLE_STICKERS", True)
ENABLE_IMAGES = get_bool("ENABLE_IMAGES", True)


# ================= DEBUG =================

DEBUG = get_bool("DEBUG", False)

if DEBUG:
    print("⚙️ DEBUG MODE ENABLED")


# ================= STARTUP LOG =================

print("✅ Config Loaded (Pro Mode)")