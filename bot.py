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
from ai import generate_reply, generate_tag_message

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 123456789  # ⚠️ replace with your Telegram ID


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "hii 😚 main aa gayi… miss kiya kya? 😏"
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai baby 😌")


# ================= TAG ALL =================

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("❌ group me use karo")

    members = context.application.bot_data.get("members", [])

    if not members:
        return await update.message.reply_text("koi active hi nahi hai 😴")

    msg = "📢 suno sab:\n\n"

    for user in members[:10]:  # limit 10 users
        name = user["name"]
        ai_msg = await generate_tag_message(name)
        msg += f"{name} — {ai_msg}\n"

    await update.message.reply_text(msg)


# ================= LEADERBOARD =================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users()

    if not top_users:
        return await update.message.reply_text("abhi koi active nahi hai 😴")

    text = "🏆 top active log:\n\n"

    for i, user in enumerate(top_users, start=1):
        text += f"{i}. {user['name']} — {user.get('messages', 0)} 🔥\n"

    await update.message.reply_text(text)


# ================= DATABASE =================

async def database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(get_top_users(1000))
    await update.message.reply_text(f"📊 total users: {total}")


# ================= REVIVE =================

async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inactive = get_inactive_users()

    if not inactive:
        return

    names = [u["name"] for u in inactive[:5]]

    msg = f"{', '.join(names)} kaha gayab ho gaye sab 😏"

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

    await update.message.reply_text("broadcast done 😌")


# ================= AI MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    name = user.first_name
    text = update.message.text
    chat_type = update.message.chat.type

    bot_username = context.bot.username.lower()
    is_reply = update.message.reply_to_message

    # ✅ Save group
    chat_id = update.message.chat_id
    groups = context.application.bot_data.setdefault("groups", [])
    if chat_id not in groups:
        groups.append(chat_id)

    # ✅ Save members for tagall
    members = context.application.bot_data.setdefault("members", [])
    if not any(u["id"] == user.id for u in members):
        members.append({"id": user.id, "name": name})

    # ✅ Save user to DB
    update_user(user.id, name)

    # ✅ Smart trigger (ANTI-SPAM)
    if chat_type in ["group", "supergroup"]:
        if (
            f"@{bot_username}" not in text.lower()
            and "@admin" not in text.lower()
            and not is_reply
        ):
            return

    # 💅 REAL AI RESPONSE (DeepSeek)
    reply = await generate_reply(user.id, name, text)

    await update.message.reply_text(reply)


# ================= AUTO MESSAGE =================

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    groups = context.application.bot_data.get("groups", [])

    msgs = [
        "group itna silent kyu hai 😴",
        "koi baat karega ya main hi start karu? 😏",
        "ignore kar rahe ho ya busy ho sab 😌",
    ]

    for chat_id in groups:
        try:
            await context.bot.send_message(chat_id, random.choice(msgs))
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

    # Auto message every 2 hours
    app.job_queue.run_repeating(auto_message, interval=7200, first=60)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()