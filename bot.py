import os
import logging
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== CONFIG ==================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello!\n\n"
        "I'm your AI Group Bot 🤖\n\n"
        "Commands:\n"
        "/tagall - tag everyone\n"
        "/leaderboard - show active users\n"
        "/database - stats\n"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working!")

# ================== GROUP FEATURES ==================

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("❌ Use in group only")

    text = "📢 Attention everyone!\n\n@all"
    await update.message.reply_text(text)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # placeholder (upgrade later)
    text = "🏆 Leaderboard:\n\n1. 🔥 ActiveUser\n2. 💬 ChatKing\n3. 🤖 BotFan"
    await update.message.reply_text(text)

async def database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # placeholder (upgrade later)
    await update.message.reply_text("📊 Total users: 0\n👥 Groups: 0")

# ================== AI RESPONSE ==================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_type = update.message.chat.type

    bot_username = context.bot.username.lower()
    is_reply = update.message.reply_to_message

    # 👉 GROUP FILTER (SMART)
    if chat_type in ["group", "supergroup"]:
        if (
            f"@{bot_username}" not in text.lower()
            and "@admin" not in text.lower()
            and not is_reply
        ):
            return

    # 👉 SIMPLE AI STYLE REPLIES
    responses = [
        "😂 That's funny!",
        "Hmm interesting 🤔",
        "Tell me more 👀",
        "I agree 😎",
        "That's wild 🔥",
        "No way 😭",
    ]

    reply = random.choice(responses)

    await update.message.reply_text(reply)

# ================== MAIN ==================

def main():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN not found in environment variables")

    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)

# ================== RUN ==================

if __name__ == "__main__":
    main()