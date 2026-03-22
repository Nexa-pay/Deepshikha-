import os
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

from database import update_user
from ai import generate_reply

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hii… bolo kya baat hai 😏")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("AI active hai 😌")


# ================= MAIN =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        user = update.message.from_user
        text = update.message.text.strip()
        chat_id = update.message.chat_id

        # save user
        update_user(user.id, user.first_name)

        print("📩 USER:", text)

        # ================= AI =================
        reply = await generate_reply(user.id, user.first_name, text)

        print("🤖 AI:", reply)

        # ================= HUMAN DELAY =================
        delay = random.randint(2, 5)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(
                chat_id=chat_id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

    except Exception as e:
        print("❌ ERROR:", e)
        await update.message.reply_text("thoda issue hai… phir try karo 😌")


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 AI Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()