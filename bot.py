import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Logging
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN:", TOKEN)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START COMMAND RECEIVED")
    await update.message.reply_text("Bot is working 🚀")

# TEST
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("TEST COMMAND RECEIVED")
    await update.message.reply_text("Test success ✅")

# MESSAGE
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("MESSAGE RECEIVED:", update.message.text)
    await update.message.reply_text("I got your message!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()