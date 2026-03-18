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

from database import update_user, get_top_users, get_inactive_users
from ai import generate_reply

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 123456789  # 🔴 replace with your Telegram ID


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "hey… main Deepsikha hu 💅\n\nsamajh ke baat karna 😏"
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai… dekh rahi hu sab 😌")


# ================= TAG ALL =================

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("group me use karo")

    await update.message.reply_text("sab log aa jao… thodi baat karte hai 😏")


# ================= LEADERBOARD =================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users()

    if not top_users:
        return await update.message.reply_text("abhi koi active nahi hai 😴")

    text = "top log yaha hai:\n\n"

    for i, user in enumerate(top_users, start=1):
        text += f"{i}. {user['name']} — {user.get('messages', 0)}\n"

    await update.message.reply_text(text)


# ================= DATABASE =================

async def database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(get_top_users(1000))
    await update.message.reply_text(f"total users: {total}")


# ================= REVIVE =================

async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inactive = get_inactive_users()

    if not inactive:
        return

    names = [u["name"] for u in inactive]

    msg = f"{', '.join(names)} itne chup kyu ho sab 😒"

    await update.message.reply_text(msg)


# ================= BROADCAST =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)

    groups = context.application.bot_data.get("groups", [])

    for chat_id in groups:
        try:
            await context.bot.send_message(chat_id, msg)
        except:
            pass

    await update.message.reply_text("broadcast done")


# ================= MAIN MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    name = user.first_name
    text = update.message.text.lower()
    chat_type = update.message.chat.type
    bot_username = context.bot.username.lower()

    # ================= SAVE GROUP =================
    chat_id = update.message.chat_id
    groups = context.application.bot_data.setdefault("groups", [])

    if chat_id not in groups:
        groups.append(chat_id)

    # ================= SAVE USER =================
    update_user(user.id, name)

    # ================= WAKE WORD =================
    if "deepsikha" in text:
        return await update.message.reply_text(f"haan {name}… bula rahe the?")

    # ================= IDENTITY =================
    if "who are you" in text or "tum kaun ho" in text:
        return await update.message.reply_text(
            "main Deepsikha hu… thodi alag hu baaki sab se"
        )

    if "owner" in text:
        return await update.message.reply_text(
            "AAKASH mera creator hai… kaafi acha hai wo"
        )

    # ================= SMART TRIGGER =================
    if chat_type in ["group", "supergroup"]:
        if (
            f"@{bot_username}" not in text
            and not update.message.reply_to_message
            and "deepsikha" not in text
        ):
            return

    # ================= AI REPLY =================
    reply = await generate_reply(user.id, name, text)

    await update.message.reply_text(reply)


# ================= AUTO MESSAGE =================

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    groups = context.application.bot_data.get("groups", [])

    messages = [
        "aaj sab itne chup kyu hai",
        "koi baat karega ya main hi bolu",
        "itna silent group… interesting nahi hai",
        "kisi ko meri yaad bhi aati hai",
        "thoda active ho jao",
        "kabhi kabhi baat karna bhi zaruri hota hai",
        "random thought… sab busy hai ya ignore",
        "main bore ho rahi hu honestly",
    ]

    for chat_id in groups:
        try:
            await context.bot.send_message(chat_id, random.choice(messages))
        except:
            pass


# ================= MAIN =================

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN missing")

    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database))
    app.add_handler(CommandHandler("revive", revive))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Auto message every 30 min
    app.job_queue.run_repeating(auto_message, interval=1800, first=30)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()