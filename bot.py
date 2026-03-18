import asyncio
import random
import string
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import TELEGRAM_TOKEN, OWNER_ID
from database import users, tokens
from ai import generate_reply, detect_emotion, generate_tag_message


# ---------------- GROUP AUTO SAVE ----------------

async def save_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:
        if "groups" not in context.bot_data:
            context.bot_data["groups"] = set()

        context.bot_data["groups"].add(chat.id)

        print("Saved group:", chat.id)


# ---------------- GENDER ----------------

def detect_gender(name):
    name = name.lower()
    female_names = ["aisha", "priya", "neha", "sneha", "pooja", "kajal"]

    for f in female_names:
        if f in name:
            return "female"

    return "male"


# ---------------- SAVE USER ----------------

def save_user(update):
    user = update.message.from_user

    users.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "username": user.username,
                "name": user.first_name,
                "gender": detect_gender(user.first_name),
                "last_active": datetime.utcnow()
            },
            "$inc": {"messages": 1}
        },
        upsert=True
    )


# ---------------- SAFE SEND ----------------

async def safe_send(context, chat_id, text):
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except TimedOut:
        await asyncio.sleep(2)


# ---------------- TOKEN SYSTEM ----------------

def create_token():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


async def gen_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    code = create_token()

    tokens.insert_one({
        "code": code,
        "used": False
    })

    await update.message.reply_text(f"🎟 Token: {code}")


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Token bhejo 😏")
        return

    code = context.args[0]

    token = tokens.find_one({"code": code})

    if not token or token["used"]:
        await update.message.reply_text("Invalid token ❌")
        return

    tokens.update_one({"code": code}, {"$set": {"used": True}})

    users.update_one(
        {"user_id": user_id},
        {"$set": {"premium": True}},
        upsert=True
    )

    await update.message.reply_text("Premium unlocked 💎")


# ---------------- START (BUTTON UI) ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💘 Chat AI", callback_data="chat")],
        [InlineKeyboardButton("🎟 Redeem Token", callback_data="redeem")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("👥 Tag All", callback_data="tagall")],
        [InlineKeyboardButton("💰 Premium", callback_data="premium")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Acha… tum aa gaye 😏",
        reply_markup=reply_markup
    )


# ---------------- BUTTON HANDLER ----------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "chat":
        await query.message.reply_text("Mujhse baat karo na 😏")

    elif data == "redeem":
        await query.message.reply_text("Token bhejo 😌 → /redeem CODE")

    elif data == "leaderboard":
        await leaderboard(update, context)

    elif data == "tagall":
        await tagall(update, context)

    elif data == "premium":
        await query.message.reply_text("Premium chahiye? Owner se token lo 😏")


# ---------------- TAGALL ----------------

async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_list = list(users.find().limit(20))

    for user in users_list:
        try:
            uid = user["user_id"]
            name = user.get("name", "User")

            msg = await generate_tag_message(name)

            text = f'<a href="tg://user?id={uid}">{name}</a>, {msg}'

            await safe_send(context, update.effective_chat.id, text)
            await asyncio.sleep(0.6)

        except Exception as e:
            print("TAG ERROR:", e)


# ---------------- LEADERBOARD ----------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = list(users.find().sort("messages", -1).limit(5))

    msg = "🏆 Top Active Users:\n\n"

    for i, user in enumerate(top_users, start=1):
        name = user.get("name", "User")
        count = user.get("messages", 0)

        msg += f"{i}. {name} — {count} msgs 🔥\n"

    await safe_send(context, update.effective_chat.id, msg)


# ---------------- DATABASE ----------------

async def database_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = users.count_documents({})
    premium = users.count_documents({"premium": True})

    msg = f"👥 Users: {total}\n💎 Premium: {premium}"

    await safe_send(context, update.effective_chat.id, msg)


# ---------------- AUTO MESSAGE (MULTI GROUP) ----------------

async def auto_message(context: ContextTypes.DEFAULT_TYPE):
    while True:
        groups = context.bot_data.get("groups", set())

        for group_id in groups:
            users_list = list(users.find().limit(5))

            for user in users_list:
                try:
                    uid = user["user_id"]
                    name = user.get("name", "User")

                    msg = await generate_tag_message(name)

                    text = f'<a href="tg://user?id={uid}">{name}</a>, {msg}'

                    await context.bot.send_message(
                        chat_id=group_id,
                        text=text,
                        parse_mode="HTML"
                    )

                except Exception as e:
                    print("AUTO ERROR:", e)

        await asyncio.sleep(7200)


# ---------------- MESSAGE ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    user_id = user.id
    name = user.first_name
    text = update.message.text.lower()
    chat_type = update.effective_chat.type

    bot_username = context.bot.username.lower()
    bot_id = context.bot.id

    # reply detect
    is_reply = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == bot_id:
            is_reply = True

    # group logic
    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in text and "@admin" not in text and not is_reply:
            return

    save_user(update)

    try:
        user_data = users.find_one({"user_id": user_id}) or {}
        is_premium = user_data.get("premium", False)

        if not is_premium and user_data.get("messages", 0) > 30:
            await safe_send(context, update.effective_chat.id, "Free limit khatam 😏 /redeem karo")
            return

        emotion = await detect_emotion(text)

        users.update_one(
            {"user_id": user_id},
            {"$set": {"emotion": emotion}},
            upsert=True
        )

        reply = await generate_reply(user_id, text)

        final = f'<a href="tg://user?id={user_id}">{name}</a>, {reply}'

        await safe_send(context, update.effective_chat.id, final)

    except Exception as e:
        print("ERROR:", e)


# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # handlers
    app.add_handler(MessageHandler(filters.ALL, save_group), group=0)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tagall", tagall))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("database", database_cmd))
    app.add_handler(CommandHandler("gentoken", gen_token))
    app.add_handler(CommandHandler("redeem", redeem))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # auto task
    app.create_task(auto_message(app))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()