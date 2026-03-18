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


# ---------------- SAFE SEND ----------------

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
    bot_id = context.bot.id

    print("CHAT:", chat_type)
    print("USER:", user_id)
    print("TEXT:", text)

    # ---------------- GROUP LOGIC ----------------

    is_reply_to_bot = False

    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        if replied_user and replied_user.id == bot_id:
            is_reply_to_bot = True

    if chat_type in ["group", "supergroup"]:
        is_mention = f"@{bot_username}" in text
        is_admin_call = "@admin" in text

        # ❌ Ignore if none triggered
        if not (is_mention or is_admin_call or is_reply_to_bot):
            return

    # ---------------- SAVE USER ----------------

    save_user(update)

    try:
        # Emotion detection
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

        # ---------------- SMART REPLY STYLE ----------------

        if is_reply_to_bot:
            # natural reply (no name)
            final_reply = reply
        else:
            # mention user
            final_reply = f"<b>{name}</b>, {reply}"

        # ---------------- SEND ----------------

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