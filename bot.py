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


# ---------------- GENDER DETECT ----------------

def detect_gender(name):
    name = name.lower()

    female_names = ["aisha", "priya", "neha", "sneha", "pooja", "kajal"]

    for f in female_names:
        if f in name:
            return "female"

    return "male"


# ---------------- SAVE USER ----------------

def save_user(update):
    user = update.message.from_user
    name = user.first_name

    gender = detect_gender(name)

    users.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "username": user.username,
                "name": name,
                "gender": gender,
                "last_active": datetime.utcnow()
            },
            "$inc": {"messages": 1}
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
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return
        except TimedOut:
            await asyncio.sleep(2)
        except Exception as e:
            print("SEND ERROR:", e)
            return


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send(context, update.effective_chat.id, "Hey… tum aa gaye 😌")


# ---------------- TAGALL (AI PERSONALIZED) ----------------

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_list = list(users.find().limit(20))

    for user in users_list:
        try:
            uid = user["user_id"]
            name = user.get("name", "User")

            prompt = f"Call {name} in group in fun teasing Hinglish way"

            reply = await generate_reply(uid, prompt)

            message = f'<a href="tg://user?id={uid}">{name}</a>, {reply}'

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode="HTML"
            )

            await asyncio.sleep(1)

        except Exception as e:
            print("TAG ERROR:", e)


# ---------------- MESSAGE ----------------

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

    # reply detect
    is_reply = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == bot_id:
            is_reply = True

    # group logic
    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in text and "@admin" not in text and not is_reply:
            return

    save_user(update)

    try:
        emotion = await detect_emotion(text)

        users.update_one(
            {"user_id": user_id},
            {"$set": {"emotion": emotion}},
            upsert=True
        )

        reply = await generate_reply(user_id, text)

        if not reply:
            reply = "Tum ajeeb ho 😏"

        final = f'<a href="tg://user?id={user_id}">{name}</a>, {reply}'

        await safe_send(context, update.effective_chat.id, final)

    except Exception as e:
        print("ERROR:", e)


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()