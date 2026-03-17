import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import TELEGRAM_TOKEN, OWNER_ID
from database import users
from ai import generate_reply, detect_emotion


# ------------------ SAVE USER ------------------

def save_user(update):
    user = update.message.from_user

    users.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "username": user.username,
                "name": user.first_name,
                "last_active": datetime.utcnow()
            }
        },
        upsert=True
    )


# ------------------ START COMMAND ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey… you came back 😌")


# ------------------ MESSAGE HANDLER ------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("MESSAGE RECEIVED")

    if not update.message or not update.message.text:
        print("NO MESSAGE")
        return

    user_id = update.message.from_user.id
    text = update.message.text

    print("USER:", user_id)
    print("TEXT:", text)

    # Save user
    save_user(update)

    # Detect emotion
    emotion = await detect_emotion(text)

    users.update_one(
        {"user_id": user_id},
        {"$set": {"emotion": emotion}},
        upsert=True
    )

    try:
        reply = await generate_reply(user_id, text)
        print("AI REPLY:", reply)

        if not reply:
            reply = "Hmm… say that again 😏"

        await update.message.reply_text(reply)

    except Exception as e:
        print("AI ERROR:", e)
        await update.message.reply_text("Something went wrong 😅")


# ------------------ MAIN ------------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()