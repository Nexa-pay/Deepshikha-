import logging
import random
import asyncio

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, MIN_DELAY, MAX_DELAY
from database import update_user
from ai import generate_reply

logging.basicConfig(level=logging.INFO)


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("finally aaye tum 😏")


# ================= MAIN =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        user = update.message.from_user
        text = update.message.text.strip()
        chat_id = update.message.chat_id

        update_user(user.id, user.first_name)

        # ================= AI =================
        reply = await generate_reply(user.id, user.first_name, text)

        # ================= HUMAN DELAY =================
        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(
                chat_id=chat_id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

    except Exception as e:
        print("Handler error:", e)


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()