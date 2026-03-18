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


# ---------------- SAFE SEND (FIX TIMEOUT) ----------------

async def safe_send(context, chat_id, text):
    for i in range(3):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML"
            )
            return
        except TimedOut:
            print(f"Retry {i+1} sending...")
            await asyncio.sleep(2)
        except Exception as e:
            print("SEND ERROR:", e)
            return


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send(
        context,
        update.effective_chat.id,
        "Hey… you came back 😌"
    )


# ---------------- MESSAGE HANDLER ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    user_id = user.id
    name = user.first_name
    text = update.message.text.lower()
    chat_type = update.effective_chat.type

    bot_username = context.bot.username.lower()

    print("CHAT:", chat_type)
    print("USER:", user_id)
    print("TEXT:", text)

    # ---------------- GROUP LOGIC ----------------

    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in text and "@admin" not in text:
            return

    # ---------------- SAVE USER ----------------

    save_user(update)

    try:
        # Emotion tracking
        emotion = await detect_emotion(text)

        users.update_one(
            {"user_id": user_id},
            {"$set": {"emotion": emotion}},
            upsert=True
        )

        # AI reply
        reply = await generate_reply(user_id, text)
        print("AI:", reply)

        if not reply:
            reply = "Say that again 😏"

        # ✅ Mention user (HTML bold)
        final_reply = f"<b>{name}</b>, {reply}"

        # Send safely
        await safe_send(context, update.effective_chat.id, final_reply)

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