import asyncio
import random
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

from config import TELEGRAM_TOKEN, OWNER_ID, GROUP_ID
from database import users, tokens, admins
from ai import generate_reply, detect_emotion


# ------------------ HELPERS ------------------

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    return admins.find_one({"user_id": user_id}) is not None


def save_user(update):
    user = update.message.from_user

    users.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "username": user.username,
                "name": user.first_name,
                "last_active": datetime.utcnow()
            },
            "$inc": {"xp": 5, "messages": 1}
        },
        upsert=True
    )


def update_relationship(user_id, text):
    score = 1
    if "miss" in text.lower():
        score += 3

    users.update_one(
        {"user_id": user_id},
        {"$inc": {"attachment_score": score}}
    )


# ------------------ COMMANDS ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey… you came back 😌")


async def redeem(update, context):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Usage: /redeem CODE")
        return

    code = context.args[0]

    token = tokens.find_one({"code": code})

    if not token or token.get("used"):
        await update.message.reply_text("Invalid token ❌")
        return

    tokens.update_one({"code": code}, {"$set": {"used": True}})
    users.update_one({"user_id": user_id}, {"$set": {"premium": True}}, upsert=True)

    await update.message.reply_text("Premium unlocked 💎")


async def broadcast(update, context):
    if not is_admin(update.message.from_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    msg = " ".join(context.args)

    for user in users.find():
        try:
            await context.bot.send_message(user["user_id"], msg)
            await asyncio.sleep(0.05)
        except:
            pass


# ------------------ AUTO AI REPLY ------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    text = update.message.text

    save_user(update)

    emotion = await detect_emotion(text)

    users.update_one(
        {"user_id": user_id},
        {"$set": {"emotion": emotion}},
        upsert=True
    )

    update_relationship(user_id, text)

    # human-like random reply
    if random.random() > 0.3:
        return

    reply = await generate_reply(user_id, text)

    await update.message.reply_text(reply)


# ------------------ AUTO ENGAGEMENT ------------------

async def auto_message(application):
    while True:
        for user in users.find().limit(10):
            last = user.get("last_active")

            if last and datetime.utcnow() - last > timedelta(hours=6):
                try:
                    await application.bot.send_message(
                        user["user_id"],
                        "You disappeared… I noticed 😏"
                    )
                except:
                    pass

        await asyncio.sleep(1800)


# ------------------ MAIN ------------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # ✅ FIX: run background task correctly
    async def post_init(application):
        application.create_task(auto_message(application))

    app.post_init = post_init

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()