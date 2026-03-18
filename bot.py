import os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    update_user,
    get_top_users,
    get_inactive_users,
    users,
    save_group,     # 🔥 NEW (DB)
    get_groups      # 🔥 NEW (DB)
)
from ai import generate_reply, generate_tag_message

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 123456789


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hii… main Deepsikha hu 😏")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")


# ================= TAG ALL =================

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("group me use karo")

    members = context.application.bot_data.get("members", [])

    if not members:
        return await update.message.reply_text("koi active nahi hai")

    msg = "📢 suno sab:\n\n"

    for user in members[:10]:
        name = user["name"]
        ai_msg = await generate_tag_message(name)
        msg += f"{name} — {ai_msg}\n"

    await update.message.reply_text(msg)


# ================= LEADERBOARD =================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users()

    if not top_users:
        return await update.message.reply_text("abhi koi active nahi hai")

    text = "🏆 active users:\n\n"

    for i, user in enumerate(top_users, start=1):
        text += f"{i}. {user['name']} — {user.get('messages', 0)} 🔥\n"

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

    names = [u["name"] for u in inactive[:5]]
    msg = f"{', '.join(names)} kaha gayab ho gaye 😏"

    await update.message.reply_text(msg)


# ================= BROADCAST (FIXED 🔥) =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        return await update.message.reply_text("message bhejo")

    sent = 0

    # 🔥 GROUPS FROM DATABASE (FIXED)
    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, msg)
            sent += 1
        except:
            pass

    # 🔥 USERS
    for u in users.find():
        try:
            await context.bot.send_message(u["user_id"], msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"broadcast done… {sent} places 😏")


# ================= MAIN MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    name = user.first_name
    text = update.message.text.strip()
    text_lower = text.lower()
    chat_type = update.message.chat.type

    bot_username = context.bot.username.lower()
    is_reply = update.message.reply_to_message

    chat_id = update.message.chat_id

    # 🔥 SAVE GROUP IN DATABASE (PERMANENT FIX)
    if chat_type in ["group", "supergroup"]:
        save_group(chat_id)

    # SAVE MEMBERS (RAM)
    members = context.application.bot_data.setdefault("members", [])
    if not any(u["id"] == user.id for u in members):
        members.append({"id": user.id, "name": name})

    # SAVE USER
    update_user(user.id, name)

    # ================= QUICK RESPONSES =================

    if "who are you" in text_lower or "tum kaun ho" in text_lower:
        return await update.message.reply_text(
            "main Deepsikha hu… thodi alag hu sab se 😌"
        )

    if "owner" in text_lower:
        return await update.message.reply_text(
            "AAKASH mera creator hai… kaafi special hai wo 😏"
        )

    # ================= SMART TRIGGER =================

    triggered = False

    if chat_type == "private":
        triggered = True
    elif f"@{bot_username}" in text_lower:
        triggered = True
    elif is_reply and is_reply.from_user and is_reply.from_user.id == context.bot.id:
        triggered = True
    elif "@admin" in text_lower:
        triggered = True
    elif "deepsikha" in text_lower:   # 🔥 FULL WAKE (ANYWHERE)
        triggered = True

    if not triggered:
        return

    # ================= AI RESPONSE =================

    try:
        reply = await generate_reply(user.id, name, text)
    except Exception as e:
        print("Reply Error:", e)
        return await update.message.reply_text("thoda network issue hai… phir bolo 😌")

    # ================= HUMAN DELAY =================

    try:
        if len(text.split()) <= 2:
            delay = random.randint(2, 5)
        elif any(x in text_lower for x in ["love", "miss", "jaan"]):
            delay = random.randint(1, 3)
        else:
            delay = random.randint(2, 6)

        # typing effect
        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

    except:
        pass

    # ================= SEND =================
    await update.message.reply_text(reply)


# ================= AUTO MESSAGE =================

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    msgs = [
        "aaj sab itne chup kyu hai",
        "koi baat karega ya sab busy hai",
        "itna silent group… interesting nahi hai",
        "kisi ko meri yaad bhi aati hai",
        "kabhi kabhi effort dono side se hota hai",
        "main bore ho rahi hu honestly",
    ]

    for chat_id in get_groups():   # 🔥 DB GROUPS
        try:
            await context.bot.send_message(chat_id, random.choice(msgs))
        except:
            pass


# ================= MAIN =================

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN missing")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database))
    app.add_handler(CommandHandler("revive", revive))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 🔥 AUTO MESSAGE LOOP
    app.job_queue.run_repeating(auto_message, interval=1800, first=60)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()