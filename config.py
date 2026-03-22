import os

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

MODEL = "meta-llama/Llama-3-8b-chat-hf"
HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"

TEMPERATURE = 0.7
MAX_TOKENS = 60

MIN_DELAY = 2
MAX_DELAY = 5

print("✅ Config Loaded")