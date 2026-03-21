import logging
import random
import asyncio
import time

from database import update_user

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    MIN_DELAY,
    MAX_DELAY,
    PHOTO_CHANCE
)

from ai import (
    generate_reply,
    get_random_image,
    should_send_image
)

logging.basicConfig(level=logging.INFO)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    update_user(user.id, user.first_name)

    await update.message.reply_text("finally aaye tum 😏")


# ================= TEST =================
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")


# ================= MAIN HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

        if not update.message.text:
            return

        chat_id = update.message.chat_id
        user = update.message.from_user

        if not user:
            return

        text = update.message.text.strip()
        text_lower = text.lower()

        print("📩 MESSAGE:", text)

        update_user(user.id, user.first_name)

        # ================= IMAGE =================
        if should_send_image(text):
            if random.randint(1, 100) <= PHOTO_CHANCE:
                print("📸 Sending image")
                await context.bot.send_photo(chat_id, get_random_image())
            return

        # ================= TRIGGER FIX =================
        chat_type = update.message.chat.type
        bot_username = (context.bot.username or "").lower()

        triggered = (
            True  # ✅ FORCE ENABLE (fix for now)
        )

        if not triggered:
            print("❌ Not triggered")
            return

        print("✅ TRIGGERED → Calling AI")

        # ================= AI REPLY =================
        reply = await generate_reply(user.id, user.first_name, text)

        print("🤖 AI REPLY:", reply)

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
        print("❌ Handler error:", e)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()