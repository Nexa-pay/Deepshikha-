import os
import logging
import random
import asyncio
from telegram import Update, ChatMemberUpdated
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
)

# ================= SAFE DATABASE IMPORT =================
try:
    from database import (
        update_user,
        get_top_users,
        get_inactive_users,
        users,
        save_group,
        get_groups
    )
except ImportError:
    from database import (
        update_user,
        get_top_users,
        users,
        save_group,
        get_groups
    )

    # ✅ fallback if function missing
    def get_inactive_users():
        return []

# ================= SAFE AI IMPORT =================
try:
    from ai import generate_reply, generate_tag_message
except ImportError:
    from ai import generate_reply

    async def generate_tag_message(name):
        return f"{name}… kahan ho 😏"


# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 123456789


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hii… main Deepsikha hu 😏")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")


# ================= AUTO GROUP DETECT =================
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMemberUpdated = update.my_chat_member

    if result.new_chat_member.status in ["member", "administrator"]:
        chat_id = result.chat.id
        save_group(chat_id)

        try:
            await context.bot.send_message(
                chat_id,
                "hii… main Deepsikha hu 😏 ab thoda interesting hoga yaha"
            )
        except:
            pass


# ================= WELCOME SYSTEM =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        name = member.first_name

        await asyncio.sleep(random.randint(1, 3))

        msg = random.choice([
            f"{name}… late aaye ho 😏",
            f"welcome {name}… dekhte hai kitne interesting ho",
            f"{name} aa gaye… ab group thoda better hoga shayad",
            f"{name}… silent rehna better hai 😌",
        ])

        await update.message.reply_text(msg)


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


# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        return await update.message.reply_text("message bhejo")

    sent = 0

    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, msg)
            sent += 1
        except:
            pass

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

    if chat_type in ["group", "supergroup"]:
        save_group(chat_id)

    update_user(user.id, name)

    # ================= TRIGGER =================
    triggered = (
        chat_type == "private"
        or f"@{bot_username}" in text_lower
        or (is_reply and is_reply.from_user and is_reply.from_user.id == context.bot.id)
        or "deepsikha" in text_lower
    )

    if not triggered:
        return

    # ================= AI =================
    try:
        reply = await generate_reply(user.id, name, text)
    except:
        return await update.message.reply_text("thoda issue hai… phir bolo 😌")

    # ================= DELAY =================
    delay = random.randint(2, 6)

    for _ in range(max(1, delay // 2)):
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(1)

    await asyncio.sleep(delay / 2)

    await update.message.reply_text(reply)


# ================= AUTO MESSAGE =================
async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    msgs = [
        "aaj sab itne chup kyu hai",
        "koi baat karega ya sab busy hai",
        "itna silent group… interesting nahi hai",
        "kisi ko meri yaad bhi aati hai",
    ]

    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, random.choice(msgs))
        except:
            pass


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database))
    app.add_handler(CommandHandler("revive", revive))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(ChatMemberHandler(bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(auto_message, interval=1800, first=60)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()