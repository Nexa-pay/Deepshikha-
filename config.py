import os

# ================= CORE API KEYS =================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY missing")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI missing")


# ================= OWNER =================

try:
    OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
except:
    OWNER_ID = 123456789


# ================= AI MODEL CONFIG =================

MODEL = os.getenv("MODEL", "deepseek/deepseek-chat")

try:
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
except:
    TEMPERATURE = 0.7

try:
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 80))
except:
    MAX_TOKENS = 80


# ================= HUMAN BEHAVIOR =================

try:
    MIN_DELAY = int(os.getenv("MIN_DELAY", 2))
    MAX_DELAY = int(os.getenv("MAX_DELAY", 6))
except:
    MIN_DELAY = 2
    MAX_DELAY = 6

# typing probability (future use 🔥)
try:
    TYPING_PROBABILITY = int(os.getenv("TYPING_PROBABILITY", 100))
except:
    TYPING_PROBABILITY = 100


# ================= AUTO SYSTEM =================

try:
    AUTO_MESSAGE_INTERVAL = int(os.getenv("AUTO_MESSAGE_INTERVAL", 1800))
except:
    AUTO_MESSAGE_INTERVAL = 1800


# ================= EMOTIONAL SYSTEM (🔥 CONTROL PANEL) =================

try:
    JEALOUSY_CHANCE = int(os.getenv("JEALOUSY_CHANCE", 12))
except:
    JEALOUSY_CHANCE = 12

try:
    RANDOM_MESSAGE_CHANCE = int(os.getenv("RANDOM_MESSAGE_CHANCE", 8))
except:
    RANDOM_MESSAGE_CHANCE = 8

try:
    ATTACHMENT_GAIN = int(os.getenv("ATTACHMENT_GAIN", 2))
except:
    ATTACHMENT_GAIN = 2


# ================= DEBUG =================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if DEBUG:
    print("⚙️ DEBUG MODE ENABLED")