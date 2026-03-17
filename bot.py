# ------------------ AUTO AI REPLY ------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("MESSAGE RECEIVED")

    if not update.message:
        print("NO MESSAGE OBJECT")
        return

    text = update.message.text
    user_id = update.message.from_user.id

    print("USER:", user_id)
    print("TEXT:", text)

    # TEST reply (to confirm bot working)
    await update.message.reply_text("I GOT YOUR MESSAGE ✅")

    try:
        reply = await generate_reply(user_id, text)
        print("AI REPLY:", reply)

        if not reply:
            reply = "Hmm… say that again 😏"

        await update.message.reply_text(reply)

    except Exception as e:
        print("AI ERROR:", e)
        await update.message.reply_text("AI failed 😅")