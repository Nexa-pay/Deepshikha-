import os

# ================= API =================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY missing")


# ================= MODEL =================

MODEL = "deepseek/deepseek-chat"
TEMPERATURE = 0.7
MAX_TOKENS = 80


# ================= BOT =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")


# ================= DATABASE =================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")


# ================= DELAY =================

MIN_DELAY = 2
MAX_DELAY = 5


print("✅ Config Loaded")