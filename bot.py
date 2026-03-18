import asyncio
from datetime import datetime
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

from config import TELEGRAM_TOKEN
from database import users, groups
from ai import generate_reply, detect_emotion


# ---------------- SAVE GROUP ----------------

async def save_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        groups.update_one(
            {"chat_id": update.effective_chat.id},
            {"$set": {"title": update.effective_chat.title}},
            upsert=True
        )


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
    for _ in range(3):
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


# ---------------- TAGALL ----------------

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_list = list(users.find().limit(20))

    for user in users_list:
        try:
            uid = user["user_id"]
            name = user.get("name", "User")

            prompt = f"Call {name} in short fun Hinglish message"

            reply = await generate_reply(uid, prompt)

            msg = f'<a href="tg://user?id={uid}">{name}</a> {reply}'

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode="HTML"
            )

            await asyncio.sleep(1)

        except Exception as e:
            print("TAG ERROR:", e)


# ---------------- LEADERBOARD ----------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = list(users.find().sort("messages", -1).limit(5))

    text = "🔥 Top Active Users:\n\n"

    for i, u in enumerate(top, 1):
        text += f"{i}. {u.get('name')} - {u.get('messages')} msgs\n"

    await safe_send(context, update.effective_chat.id, text)


# ---------------- DATABASE ----------------

async def database_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = users.count_documents({})
    await safe_send(context, update.effective_chat.id, f"👥 Total Users: {count}")


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

        final = f'<a href="tg://user?id={user_id}">{name}</a> {reply}'

        await safe_send(context, update.effective_chat.id, final)

    except Exception as e:
        print("ERROR:", e)


# ---------------- AUTO MESSAGE (FIXED) ----------------

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    all_groups = list(groups.find())

    for g in all_groups:
        try:
            msg = await generate_reply(0, "Send short engaging Hinglish group message")
            await context.bot.send_message(chat_id=g["chat_id"], text=msg)
            await asyncio.sleep(1)
        except Exception as e:
            print("AUTO MSG ERROR:", e)


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # auto save groups
    app.add_handler(MessageHandler(filters.ALL, save_group), group=0)

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database_cmd))

    # messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ✅ FIXED AUTO MESSAGE (NO ERROR)
    app.job_queue.run_repeating(auto_message, interval=7200, first=10)

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()