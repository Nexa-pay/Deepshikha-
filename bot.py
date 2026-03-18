import os
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

from database import (
    update_user,
    get_top_users,
    get_inactive_users,
    users,
    save_group,
    get_groups
)
from ai import generate_reply, generate_tag_message

# ================= CONFIG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# ================= MEDIA =================

GITHUB_IMAGES = [
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4818.jpg",
    "https://raw.githubusercontent.com/Nexa-pay/Deepshikha-/main/image/IMG_4830.jpg"
]

STICKERS = {
    "tease": [],
    "cute": [],
    "attitude": [],
    "love": []
}

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hii… main Deepsikha hu 😏")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("bot active hai 😌")

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
        name = member.first_name

        await asyncio.sleep(random.randint(1, 3))

        msg = random.choice([
            f"{name}… late aaye ho 😏",
            f"welcome {name}… dekhte hai kitne interesting ho",
            f"{name} aa gaye… ab group thoda better hoga shayad",
            f"{name}… silent rehna better hai 😌",
        ])

        await update.message.reply_text(msg)

# ================= BROADCAST =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return await update.message.reply_text("not allowed")

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

    for u in users.find():
        try:
            await context.bot.send_message(u["user_id"], msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"done 😏\nsent: {sent}\nfailed: {failed}")

# ================= MAIN =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # 🔥 STICKER ID GETTER
    if update.message.sticker:
        await update.message.reply_text(update.message.sticker.file_id)
        return

    if not update.message.text:
        return

    user = update.message.from_user
    name = user.first_name
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
    update_user(user.id, name)

    # ================= IMAGE =================

    if any(x in text_lower for x in ["photo", "pic", "selfie"]):
        if random.randint(1, 100) <= 50:
            return await update.message.reply_text("itni jaldi photo? 😏")

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=random.choice(GITHUB_IMAGES)
        )
        return

    # ================= STICKERS =================

    if any(x in text_lower for x in ["lol", "haha"]):
        if STICKERS["cute"]:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERS["cute"]))
        return

    if any(x in text_lower for x in ["miss", "love"]):
        if STICKERS["love"]:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERS["love"]))
        return

    if any(x in text_lower for x in ["ignore", "huh"]):
        if STICKERS["attitude"]:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERS["attitude"]))
        return

    # ================= JEALOUSY =================

    if chat_type in ["group", "supergroup"]:
        if "deepsikha" not in text_lower and not is_reply:
            if random.randint(1, 100) <= 12:
                return await update.message.reply_text(random.choice([
                    "hmm… mujhe ignore karke dusro se baat 😒",
                    "acha… ab main boring lag rahi hu?",
                    "mere bina bhi kaafi baate ho rahi hai 😏",
                    "thoda mujhe bhi yaad kar liya karo",
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
        reply = await generate_reply(user.id, name, text)
    except:
        return await update.message.reply_text("thoda network issue hai… phir bolo 😌")

    # ================= DELAY =================

    delay = random.randint(2, 6)

    for _ in range(max(1, delay // 2)):
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(1)

    await asyncio.sleep(delay / 2)

    await update.message.reply_text(reply)

    # ================= RANDOM REACTION =================

    if random.randint(1, 100) <= 8:
        await asyncio.sleep(random.randint(5, 15))
        await context.bot.send_message(chat_id, random.choice([
            "sab itne chup kyun hai aaj",
            "koi interesting banda hai yaha?",
            "mujhe ignore kar rahe ho kya 😒",
            "itna dead group kyun hai",
        ]))

    # 🎭 RANDOM STICKER
    if random.randint(1, 100) <= 6:
        mood = random.choice(list(STICKERS.keys()))
        if STICKERS[mood]:
            await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERS[mood]))

# ================= AUTO =================

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in get_groups():
        try:
            await context.bot.send_message(chat_id, random.choice([
                "aaj sab itne chup kyu hai",
                "koi baat karega ya sab busy hai",
                "itna silent group… interesting nahi hai",
                "kisi ko meri yaad bhi aati hai",
            ]))
        except:
            pass

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(ChatMemberHandler(bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(auto_message, interval=1800, first=60)

    print("Bot running... 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()