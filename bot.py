import logging
import random
import asyncio
import time

from database import (
    update_user,
    users,
    save_group,
    get_groups,
    get_top_users,
    get_all_users
)

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

from config import (
    BOT_TOKEN,
    OWNER_ID,
    MIN_DELAY,
    MAX_DELAY,
    PHOTO_CHANCE
)

# SAFE IMPORT
try:
    from database import (
        update_user,
        users,
        save_group,
        get_groups,
        get_top_users
    )
except ImportError:
    from database import update_user, users, save_group, get_groups
    def get_top_users():
        return []

from ai import (
    generate_reply,
    get_random_image,
    should_send_image
)

logging.basicConfig(level=logging.INFO)


# ================= MEMORY =================
def init_memory(app):
    if "last_replies" not in app.bot_data:
        app.bot_data["last_replies"] = {}

    if "last_activity" not in app.bot_data:
        app.bot_data["last_activity"] = {}

    if "active_users" not in app.bot_data:
        app.bot_data["active_users"] = {}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    update_user(user.id, user.first_name)
    await update.message.reply_text("hii… main Deepsikha hu 😏")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")


# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        return await update.message.reply_text("message bhejo")

    sent, failed = 0, 0

    for user_id in get_all_users():
        try:
            await context.bot.send_message(user_id, msg)
            sent += 1
        except:
            failed += 1

    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"done 😏\nsent: {sent}\nfailed: {failed}")


# ================= DATABASE =================
async def database_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = users.count_documents({})
    await update.message.reply_text(f"total users: {count}")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = get_top_users()

    if not top:
        return await update.message.reply_text("abhi koi active user nahi 😌")

    text = "🏆 Top users:\n\n"

    for i, u in enumerate(top, 1):
        text += f"{i}. {u.get('name','user')} — {u.get('messages',0)} msgs\n"

    await update.message.reply_text(text)


# ================= BOT ADDED =================
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMemberUpdated = update.my_chat_member

    if result.new_chat_member.status in ["member", "administrator"]:
        chat_id = result.chat.id
        save_group(chat_id)

        try:
            await context.bot.send_message(chat_id, "hii… main Deepsikha hu 😏")
        except:
            pass


# ================= MAIN =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

        init_memory(context.application)

        chat_id = update.message.chat_id
        context.application.bot_data["last_activity"][chat_id] = time.time()

        if update.message.sticker:
            return

        if not update.message.text:
            return

        user = update.message.from_user
        if not user:
            return

        text = update.message.text.strip()
        text_lower = text.lower()
        chat_type = update.message.chat.type

        bot_username = (context.bot.username or "").lower()
        is_reply = update.message.reply_to_message

        if chat_type in ["group", "supergroup"]:
            save_group(chat_id)

        update_user(user.id, user.first_name)

        # ================= IMAGE =================
        if should_send_image(text):
            if random.randint(1, 100) <= PHOTO_CHANCE:
                await context.bot.send_photo(chat_id, get_random_image())
            else:
                await update.message.reply_text("itni jaldi photo? 😏")
            return

        # ================= QUICK REPLIES =================
        quick_reply = None

        if any(x in text_lower for x in ["hi", "hello", "hey"]):
            quick_reply = "hello 🙂"

        elif "good morning" in text_lower:
            quick_reply = "good morning 🙂"

        elif "good night" in text_lower:
            quick_reply = "good night 🙂"

        elif "bye" in text_lower:
            quick_reply = "bye 🙂"

        if quick_reply:
            await update.message.reply_text(quick_reply)
            return  # ✅ FIX: stop double reply

        # ================= TRIGGER =================
        triggered = (
            chat_type == "private"
            or f"@{bot_username}" in text_lower
            or (is_reply and is_reply.from_user and is_reply.from_user.id == context.bot.id)
        )

        if not triggered:
            return

        reply = await generate_reply(user.id, user.first_name, text)

        history = context.application.bot_data["last_replies"].get(user.id, [])

        # ================= FIX REPEAT =================
        if reply in history:
            reply = random.choice([
                "hmm… aur bolo 😌",
                "acha samjha 🙂",
                "continue karo 🙂",
                "interesting 😄"
            ])

        history.append(reply)
        context.application.bot_data["last_replies"][user.id] = history[-5:]

        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

    except Exception as e:
        print("Main handler error:", e)


# ================= AUTO =================
async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in get_groups():
        try:
            last = context.application.bot_data["last_activity"].get(chat_id, 0)

            if time.time() - last > 900:
                continue

            if random.randint(1, 100) > 3:
                continue

            await context.bot.send_message(chat_id, "sab chup kyun hai 😏")

        except Exception as e:
            print("Auto message error:", e)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    init_memory(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("database", database_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    app.add_handler(ChatMemberHandler(bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(auto_message, interval=1800, first=120)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()