import os

# ================= API =================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================= MODEL =================
MODEL = "mistralai/mistral-7b-instruct"

TEMPERATURE = 0.7
MAX_TOKENS = 60

# ================= OWNER =================
OWNER_NAME = "Aakash"
OWNER_ID = 123456789

# ================= DELAY =================
MIN_DELAY = 2
MAX_DELAY = 5

# ================= IMAGE =================
PHOTO_CHANCE = 40

# ================= CHECK =================
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY missing")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

print("✅ Config Loaded")