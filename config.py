import os

# ================= API KEYS =================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY missing")


# ================= MODEL CONFIG =================

MODEL = os.getenv("MODEL", "deepseek/deepseek-chat")

TEMPERATURE = float(os.getenv("TEMPERATURE", 0.65))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 80))


# ================= BOT CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")


OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))


# ================= DATABASE =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")


# ================= OPTIONAL SETTINGS =================

# delay control (for human-like replies)
MIN_DELAY = int(os.getenv("MIN_DELAY", 2))
MAX_DELAY = int(os.getenv("MAX_DELAY", 6))

# auto message interval (seconds)
AUTO_MESSAGE_INTERVAL = int(os.getenv("AUTO_MESSAGE_INTERVAL", 1800))


# ================= DEBUG =================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"