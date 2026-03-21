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

from ai import generate_reply, get_random_image, should_send_image

logging.basicConfig(level=logging.INFO)


def init_memory(app):
    if "last_replies" not in app.bot_data:
        app.bot_data["last_replies"] = {}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    update_user(user.id, user.first_name)
    await update.message.reply_text("hii 🙂")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 🙂")


# ================= MAIN =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        chat_id = update.message.chat_id
        user = update.message.from_user
        text = update.message.text.strip()
        text_lower = text.lower()

        update_user(user.id, user.first_name)

        # ================= IMAGE =================
        if should_send_image(text):
            if random.randint(1, 100) <= PHOTO_CHANCE:
                await context.bot.send_photo(chat_id, get_random_image())
            return

        # ================= TRIGGER =================
        chat_type = update.message.chat.type
        bot_username = (context.bot.username or "").lower()

        triggered = (
            chat_type == "private"
            or f"@{bot_username}" in text_lower
            or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)
        )

        if not triggered:
            return

        reply = await generate_reply(user.id, user.first_name, text)

        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

    except Exception as e:
        print("Handler error:", e)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    init_memory(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running... 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()