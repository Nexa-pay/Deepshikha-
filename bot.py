import logging
import random
import asyncio
import time

from telegram import Update, ChatMemberUpdated
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

from database import (
    update_user,
    users,
    save_group,
    get_groups,
    get_top_users
)

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


# ================= STICKERS =================

def load_stickers():
    data = {}
    current = None

    try:
        with open("stickers/ids.txt") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    current = line.replace("#", "").strip()
                    data[current] = []
                else:
                    if current:
                        data[current].append(line)

    except Exception as e:
        print("Sticker load error:", e)

    return data


STICKERS = load_stickers()


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

    if not msg:
        return await update.message.reply_text("message bhejo")

    sent, failed = 0, 0

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
        context.application.bot_data[chat_id] = time.time()

        if update.message.sticker:
            await update.message.reply_text(update.message.sticker.file_id)
            return

        if not update.message.text:
            return

        user = update.message.from_user
        text = update.message.text.strip()
        text_lower = text.lower()
        chat_type = update.message.chat.type

        bot_username = context.bot.username.lower()
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
        reply = await generate_reply(user.id, user.first_name, text)

        # ================= ANTI-REPEAT =================
        history = context.application.bot_data["last_replies"].get(user.id, [])

        tries = 0
        while reply in history and tries < 3:
            reply = await generate_reply(user.id, user.first_name, text)
            tries += 1

        if reply in history:
            reply += random.choice([" 😏", " hmm", " acha"])

        history.append(reply)
        history = history[-5:]
        context.application.bot_data["last_replies"][user.id] = history

        # ================= DELAY =================
        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

        # ================= STICKER =================
        try:
            user_data = users.find_one({"user_id": user.id}) or {}
            relationship = int(user_data.get("relationship", 0))

            mood = detect_reply_mood(reply)

            force = any(x in text_lower for x in ["sticker", "gif", "bhej"])

            chance = min(10 + relationship // 2, 80)

            send = True if force else random.randint(1, 100) <= chance

            if send and mood in STICKERS and STICKERS[mood]:
                selected = random.choice(STICKERS[mood])

                if selected.startswith("http"):
                    await context.bot.send_animation(chat_id, selected)
                else:
                    await context.bot.send_sticker(chat_id, selected)

        except Exception as e:
            print("Sticker error:", e)

        # ================= VOICE FIX =================
        if ENABLE_VOICE and any(x in text_lower for x in ["voice", "bolo", "sunao", "audio"]):
            voice_file = await text_to_voice(reply, user.id)

            if voice_file:
                try:
                    with open(voice_file, "rb") as v:
                        await context.bot.send_voice(chat_id, v)
                except Exception as e:
                    print("Voice error:", e)

                delete_voice(voice_file)

    except Exception as e:
        print("Main handler error:", e)


# ================= AUTO =================

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in get_groups():
        try:
            last = context.application.bot_data.get(chat_id, 0)

            if time.time() - last > 900:
                continue

            if random.randint(1, 100) > 3:
                continue

            await context.bot.send_message(chat_id, "sab chup kyun hai 😏")

        except:
            pass


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

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