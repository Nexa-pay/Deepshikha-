import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from ai import generate_reply
from voice import text_to_voice
from payments import create_payment
from database import users

TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey… I was waiting for you 😉")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    link = create_payment(user_id)

    await update.message.reply_text(f"Unlock me 💎:\n{link}")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    user = users.find_one({"user_id": user_id})

    if not user or not user.get("premium"):
        await update.message.reply_text("Unlock premium first 💳 /buy")
        return

    reply = await generate_reply(user_id, text)

    voice = text_to_voice(reply, user_id)

    await update.message.reply_voice(voice=open(voice, "rb"))

    os.remove(voice)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
