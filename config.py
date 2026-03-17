import os


# ------------------ TELEGRAM ------------------

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# ------------------ OWNER / ADMIN ------------------

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))


# ------------------ DATABASE ------------------

MONGO_URI = os.getenv("MONGO_URI")


# ------------------ AI (DEEPSEEK / OPENROUTER) ------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ------------------ OPTIONAL SETTINGS ------------------

# Max tokens per reply
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "40"))

# Auto reply chance (0.3 = 30%)
REPLY_PROBABILITY = float(os.getenv("REPLY_PROBABILITY", "0.3"))

# Auto message interval (seconds)
AUTO_MESSAGE_INTERVAL = int(os.getenv("AUTO_MESSAGE_INTERVAL", "1800"))