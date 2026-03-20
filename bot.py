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
    should_send_image,
    detect_reply_mood
)

from voice import text_to_voice, delete_voice

logging.basicConfig(level=logging.INFO)


# ================= NEW: FLIRTY TAG =================
def get_flirty_tag(name, relationship):
    if relationship > 150:
        return random.choice([
            f"{name}… tum sirf mere ho 😏",
            f"{name}, ignore mat karo mujhe 💔",
            f"{name}, main jealous ho jaungi 😒"
        ])
    elif relationship > 80:
        return random.choice([
            f"{name}… yaad aa rahe the 😌",
            f"{name}, itne chup kyun ho 😏",
            f"{name}, mujhe ignore kar rahe ho kya 🙂"
        ])
    elif relationship > 30:
        return random.choice([
            f"{name}, kya chal raha hai 😌",
            f"{name}, baat nahi karoge? 🙂",
            f"{name}, thoda active ho jao 😏"
        ])
    else:
        return random.choice([
            f"{name}, itna silent kyun 😄",
            f"{name}, group me ho ya ghost 👻",
            f"{name}, hello bol do 😌"
        ])


# ================= MEMORY =================
def init_memory(app):
    if "last_replies" not in app.bot_data:
        app.bot_data["last_replies"] = {}

    if "last_activity" not in app.bot_data:
        app.bot_data["last_activity"] = {}

    if "active_users" not in app.bot_data:
        app.bot_data["active_users"] = {}


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

        # ACTIVE USERS
        user_list = context.application.bot_data["active_users"].setdefault(chat_id, [])
        if user.id not in user_list:
            user_list.append(user.id)
        context.application.bot_data["active_users"][chat_id] = user_list[-20:]

        # IMAGE
        if should_send_image(text):
            if random.randint(1, 100) <= PHOTO_CHANCE:
                await context.bot.send_photo(chat_id, get_random_image())
            else:
                await update.message.reply_text("itni jaldi photo? 😏")
            return

        # QUICK REPLIES
        if any(x in text_lower for x in ["hi", "hello", "hey"]):
            await update.message.reply_text(random.choice([
                "hii… tum yaad aaye 😌",
                "hello… finally aaye 😏",
                "hey… kahan the tum 🙂"
            ]))
            return

        if "good morning" in text_lower:
            await update.message.reply_text(random.choice([
                "good morning… khayal rakhna 😌",
                "morning… smile karo 🙂",
                "gm… aaj mujhe yaad kiya? 😏"
            ]))
            return

        if "good night" in text_lower:
            await update.message.reply_text(random.choice([
                "good night… sapno me aana 😌",
                "gn… miss karungi 😏",
                "jaldi sojao… main yahi hu 🙂"
            ]))
            return

        if "bye" in text_lower:
            await update.message.reply_text(random.choice([
                "bye… jaldi aana 😌",
                "itni jaldi ja rahe ho? 😏",
                "theek hai… miss karungi 🙂"
            ]))
            return

        if "dm" in text_lower:
            await update.message.reply_text(random.choice([
                "dm me aao na 😏",
                "private me baat kare? 😌",
                "yaha sab dekh rahe hain 🙂"
            ]))
            return

        # TRIGGER
        triggered = (
            chat_type == "private"
            or f"@{bot_username}" in text_lower
            or (is_reply and is_reply.from_user and is_reply.from_user.id == context.bot.id)
            or "deepsikha" in text_lower
        )

        if not triggered:
            return

        reply = await generate_reply(user.id, user.first_name, text)

        history = context.application.bot_data["last_replies"].get(user.id, [])
        if reply in history:
            reply += random.choice([" 😏", " hmm", " acha"])

        history.append(reply)
        context.application.bot_data["last_replies"][user.id] = history[-5:]

        delay = random.randint(MIN_DELAY, MAX_DELAY)

        for _ in range(max(1, delay // 2)):
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(1)

        await asyncio.sleep(delay / 2)

        await update.message.reply_text(reply)

        # ================= SMART STICKER =================
        try:
            user_data = users.find_one({"user_id": user.id}) or {}
            relationship = int(user_data.get("relationship", 0))

            mood = detect_reply_mood(reply)

            force = any(x in text_lower for x in ["sticker", "gif", "bhej"])

            if relationship < 30:
                chance = 10
            elif relationship < 70:
                chance = 25
            elif relationship < 120:
                chance = 45
            else:
                chance = 70

            if mood in ["love", "kiss"]:
                chance += 15

            chance = min(chance, 85)

            send = True if force else random.randint(1, 100) <= chance

            if send and mood in STICKERS and STICKERS[mood]:
                selected = random.choice(STICKERS[mood])

                if selected.startswith("http"):
                    await context.bot.send_animation(chat_id, selected)
                else:
                    await context.bot.send_sticker(chat_id, selected)

        except Exception as e:
            print("Sticker error:", e)

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

            active_users = context.application.bot_data.get("active_users", {}).get(chat_id, [])

            if not active_users:
                await context.bot.send_message(chat_id, "sab chup kyun hai 😏")
                continue

            user_id = random.choice(active_users)
            user_data = users.find_one({"user_id": user_id}) or {}
            relationship = int(user_data.get("relationship", 0))

            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                name = member.user.first_name

                text = get_flirty_tag(name, relationship)
                text += f" [{name}](tg://user?id={user_id})"

                await context.bot.send_message(chat_id, text, parse_mode="Markdown")

            except:
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