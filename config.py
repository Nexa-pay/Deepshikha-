import os

# ================= API =================
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================= MODEL =================
MODEL = "meta-llama/Llama-3-8b-chat-hf"

TEMPERATURE = 0.7
MAX_TOKENS = 60

# ================= DELAY =================
MIN_DELAY = 2
MAX_DELAY = 5

# ================= CHECK =================
if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY missing")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

print("✅ Config Loaded")