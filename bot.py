import asyncio
from datetime import datetime, timedelta
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
from ai import generate_reply, detect_emotion, generate_tag_message


# ---------------- SAVE USER ----------------

def save_user(update):
    user = update.message.from_user

    users.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "name": user.first_name,
                "last_active": datetime.utcnow()
            },
            "$inc": {"messages": 1}
        },
        upsert=True
    )


# ---------------- SAFE SEND ----------------

async def safe_send(context, chat_id, text):
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )
    except TimedOut:
        await asyncio.sleep(2)


# ---------------- TAGALL ----------------

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_list = list(users.find().limit(20))

    for user in users_list:
        uid = user["user_id"]
        name = user.get("name", "User")

        msg = await generate_tag_message(name)

        text = f'<a href="tg://user?id={uid}">{name}</a>, {msg}'

        await safe_send(context, update.effective_chat.id, text)
        await asyncio.sleep(0.6)


# ---------------- LEADERBOARD ----------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = list(users.find().sort("messages", -1).limit(5))

    msg = "🏆 Top Active Users:\n\n"

    for i, user in enumerate(top_users, start=1):
        name = user.get("name", "User")
        count = user.get("messages", 0)

        msg += f"{i}. {name} — {count} msgs 🔥\n"

    await safe_send(context, update.effective_chat.id, msg)


# ---------------- DATABASE ----------------

async def database_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = users.count_documents({})

    await safe_send(
        context,
        update.effective_chat.id,
        f"👥 Total Users: {total}"
    )


# ---------------- AUTO REVIVE ----------------

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    while True:
        users_list = list(users.find().limit(5))

        for user in users_list:
            uid = user["user_id"]
            name = user.get("name", "User")

            msg = await generate_tag_message(name)

            text = f'<a href="tg://user?id={uid}">{name}</a>, {msg}'

            try:
                await context.bot.send_message(
                    chat_id=context.job.chat_id,
                    text=text,
                    parse_mode="HTML"
                )
            except:
                pass

        await asyncio.sleep(7200)  # 2 hours


# ---------------- MESSAGE ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    text = update.message.text.lower()
    chat_type = update.effective_chat.type

    bot_username = context.bot.username.lower()
    bot_id = context.bot.id

    # reply detection
    is_reply = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == bot_id:
            is_reply = True

    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in text and not is_reply:
            return

    save_user(update)

    reply = await generate_reply(user.id, text)

    final = f'<a href="tg://user?id={user.id}">{user.first_name}</a>, {reply}'

    await safe_send(context, update.effective_chat.id, final)


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()