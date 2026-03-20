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
    PHOTO_CHANCE,
    ENABLE_VOICE
)

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
    should_send_image,
    detect_reply_mood
)

from voice import text_to_voice, delete_voice

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


# ================= BOT ADDED =================
async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member.new_chat_member.status in ["member", "administrator"]:
        chat_id = update.my_chat_member.chat.id
        save_group(chat_id)
        await context.bot.send_message(chat_id, "hii… main Deepsikha hu 😏")


# ================= MAIN =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        init_memory(context.application)

        chat_id = update.message.chat_id
        context.application.bot_data["last_activity"][chat_id] = time.time()

        user = update.message.from_user
        text = update.message.text.strip()
        text_lower = text.lower()
        chat_type = update.message.chat.type

        update_user(user.id, user.first_name)

        if chat_type in ["group", "supergroup"]:
            save_group(chat_id)

        # ================= IMAGE =================
        if should_send_image(text):
            if random.randint(1, 100) <= PHOTO_CHANCE:
                await context.bot.send_photo(chat_id, get_random_image())
            else:
                await update.message.reply_text("itni jaldi photo? 😏")
            return

        # ================= GREETING (NO BLOCK) =================
        greeting_reply = None

        if text_lower in ["hi", "hello", "hey"]:
            greeting_reply = random.choice([
                "hii… 😌",
                "hello… 😏",
                "hey… 🙂"
            ])

        elif "good morning" in text_lower:
            greeting_reply = "good morning… 😌"

        elif "good night" in text_lower:
            greeting_reply = "good night… 😏"

        elif text_lower == "bye":
            greeting_reply = "bye… jaldi aana 😌"

        # 👉 DO NOT RETURN → AI will still run

        # ================= TRIGGER =================
        bot_username = (context.bot.username or "").lower()
        is_reply = update.message.reply_to_message

        triggered = (
            chat_type == "private"
            or f"@{bot_username}" in text_lower
            or (is_reply and is_reply.from_user and is_reply.from_user.id == context.bot.id)
            or "deepsikha" in text_lower
        )

        if not triggered:
            return

        # ================= AI =================
        reply = await generate_reply(user.id, user.first_name, text)

        # ================= ANTI REPEAT =================
        history = context.application.bot_data["last_replies"].get(user.id, [])

        if reply in history:
            reply = random.choice([
                "acha aur bolo 😏",
                "hmm… interesting 😌",
                "continue karo 🙂"
            ])

        history.append(reply)
        context.application.bot_data["last_replies"][user.id] = history[-10:]

        # ================= DELAY =================
        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        # ================= FINAL REPLY =================
        if greeting_reply:
            await update.message.reply_text(greeting_reply + "\n" + reply)
        else:
            await update.message.reply_text(reply)

        # ================= STICKER =================
        try:
            mood = detect_reply_mood(reply)

            if mood:
                from random import randint, choice

                if randint(1, 100) < 40:
                    stickers = {
                        "love": ["CAACAgUAAxkBAAIBn2m6unqBOZ54pGQuWyap12yb_AQpAALfFgACoU2xVm2ASXqcHR7MOgQ"],
                        "kiss": ["CAACAgUAAxkBAAIBpWm6uoSMvzg502D3xImz1xclxcPBAAJFBgACNFDoVFpM5xQJZirUOgQ"],
                        "cute": ["CAACAgUAAxkBAAIBp2m6uuxj2Tt7PqCj2AbmSLRFAyflAAIzFQAC_VT4V-26cmC9co6dOgQ"]
                    }

                    if mood in stickers:
                        await context.bot.send_sticker(chat_id, choice(stickers[mood]))

        except Exception as e:
            print("Sticker error:", e)

    except Exception as e:
        print("Main handler error:", e)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    init_memory(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(ChatMemberHandler(bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()