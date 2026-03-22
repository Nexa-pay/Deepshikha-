import os

# ================= CORE =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN missing")


# ================= AI KEYS =================

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# (optional but recommended warning)
if not TOGETHER_API_KEY:
    print("⚠️ TOGETHER_API_KEY missing")

if not HF_API_KEY:
    print("⚠️ HF_API_KEY missing")


# ================= AI SETTINGS =================

MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

TEMPERATURE = 0.7
MAX_TOKENS = 60


# ================= HUMAN BEHAVIOR =================

MIN_DELAY = 2
MAX_DELAY = 5


# ================= START =================

print("✅ Config Loaded")