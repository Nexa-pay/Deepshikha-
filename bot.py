import asyncio
from datetime import datetime
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import TELEGRAM_TOKEN
from database import users
from ai import generate_reply, detect_emotion


# ---------------- SAVE USER ----------------

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


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send(context, update.effective_chat.id, "Hey… you came back 😌")


# ---------------- SAFE SEND (FIX TIMEOUT) ----------------

async def safe_send(context, chat_id, text):
    for i in range(3):  # retry 3 times
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            return
        except TimedOut:
            print(f"Retrying send... ({i+1})")
            await asyncio.sleep(2)
        except Exception as e:
            print("SEND ERROR:", e)
            return


# ---------------- MESSAGE ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text

    print("MESSAGE:", text)

    save_user(update)

    try:
        emotion = await detect_emotion(text)
        users.update_one({"user_id": user_id}, {"$set": {"emotion": emotion}}, upsert=True)

        reply = await generate_reply(user_id, text)
        print("AI:", reply)

        if not reply:
            reply = "Say that again 😏"

        # ✅ FIXED SEND
        await safe_send(context, update.effective_chat.id, reply)

    except Exception as e:
        print("ERROR:", e)


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()