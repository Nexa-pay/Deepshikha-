import logging
import random
import asyncio

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
    STICKER_CHANCE,
    JEALOUSY_CHANCE,
    RANDOM_MESSAGE_CHANCE,
    ENABLE_VOICE
)

from database import (
    update_user,
    users,
    save_group,
    get_groups,
    get_top_users
)

from ai import generate_reply, get_random_image, should_send_image
from voice import text_to_voice, delete_voice

logging.basicConfig(level=logging.INFO)


# ================= STICKERS =================
STICKERS = {
    "cute": [],
    "love": [],
    "attitude": [],
    "tease": []
}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hii… main Deepsikha hu 😏")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")


# ================= DATABASE =================
async def database_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = users.count_documents({})
    await update.message.reply_text(f"total users: {count}")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = get_top_users()

    if not top:
        return await update.message.reply_text("abhi koi active user nahi hai 😌")

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
            await context.bot.send_message(
                chat_id,
                "hii… main Deepsikha hu 😏 ab thoda interesting hoga yaha"
            )
        except:
            pass


# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        await asyncio.sleep(random.randint(1, 3))

        await update.message.reply_text(random.choice([
            f"{member.first_name}… late aaye ho 😏",
            f"welcome {member.first_name}… dekhte hai kitne interesting ho",
            f"{member.first_name} aa gaye… ab group better hoga shayad",
        ]))


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

    # ✅ only active users
    for u in users.find({"messages": {"$gt": 0}}):
        try:
            await context.bot.send_message(u["user_id"], msg)
            sent += 1
        except:
            failed += 1
            users.delete_one({"user_id": u["user_id"]})  # 🔥 cleanup

    await update.message.reply_text(f"done 😏\nsent: {sent}\nfailed: {failed}")


# ================= MAIN =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # 🔥 sticker id getter
    if update.message.sticker:
        await update.message.reply_text(update.message.sticker.file_id)
        return

    if not update.message.text:
        return

    user = update.message.from_user
    text = update.message.text.strip()
    text_lower = text.lower()
    chat_type = update.message.chat.type
    chat_id = update.message.chat_id

    bot_username = context.bot.username.lower()
    is_reply = update.message.reply_to_message

    # SAVE GROUP
    if chat_type in ["group", "supergroup"]:
        save_group(chat_id)

    # SAVE USER
    update_user(user.id, user.first_name)

    # ================= MEMBER TRACK =================
    members = context.application.bot_data.setdefault("members", [])
    if not any(u["id"] == user.id for u in members):
        members.append({"id": user.id, "name": user.first_name})

    # ================= IMAGE =================
    if should_send_image(text):
        if random.randint(1, 100) <= PHOTO_CHANCE:
            await context.bot.send_photo(chat_id, get_random_image())
        else:
            await update.message.reply_text("itni jaldi photo? 😏")
        return

    # ================= STICKERS =================
    if random.randint(1, 100) <= STICKER_CHANCE:
        mood = random.choice(list(STICKERS.keys()))
        if STICKERS[mood]:
            await context.bot.send_sticker(chat_id, random.choice(STICKERS[mood]))

    # ================= JEALOUSY =================
    if chat_type in ["group", "supergroup"]:
        if "deepsikha" not in text_lower and not is_reply:
            if random.randint(1, 100) <= JEALOUSY_CHANCE:
                return await update.message.reply_text(random.choice([
                    "hmm… mujhe ignore karke dusro se baat 😒",
                    "acha… ab main boring lag rahi hu?",
                    "mere bina bhi kaafi baate ho rahi hai 😏",
                ]))

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
        reply = await generate_reply(user.id, user.first_name, text)
    except:
        return await update.message.reply_text("thoda network issue hai… phir bolo 😌")

    # ================= DELAY =================
    delay = random.randint(MIN_DELAY, MAX_DELAY)

    for _ in range(max(1, delay // 2)):
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(1)

    await asyncio.sleep(delay / 2)

    await update.message.reply_text(reply)

    # ================= VOICE =================
    if ENABLE_VOICE and any(x in text_lower for x in ["voice", "bolo", "sunao"]):
        voice_file = text_to_voice(reply, user.id)

        if voice_file:
            with open(voice_file, "rb") as v:
                await update.message.reply_voice(v)

            delete_voice(voice_file)

    # ================= RANDOM MESSAGE =================
    if random.randint(1, 100) <= RANDOM_MESSAGE_CHANCE:
        await asyncio.sleep(random.randint(5, 15))

        msgs = [
            "sab itne chup kyun hai",
            "koi interesting banda hai yaha?",
            "mujhe ignore kar rahe ho kya 😒",
        ]

        await context.bot.send_message(chat_id, random.choice(msgs))

    # ================= USER CALLOUT (🔥 GROWTH) =================
    if random.randint(1, 100) <= 10 and members:
        u = random.choice(members)
        await context.bot.send_message(chat_id, f"{u['name']}… tum chup kyu ho 😏")


# ================= AUTO =================
async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, random.choice([
                "aaj sab itne chup kyu hai",
                "koi baat karega ya sab busy hai",
                "itna silent group… interesting nahi hai",
            ]))
        except:
            pass


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("database", database_cmd))     # 🔥 FIX
    app.add_handler(CommandHandler("leaderboard", leaderboard))   # 🔥 FIX

    app.add_handler(ChatMemberHandler(bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(auto_message, interval=1800, first=60)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()