from modules.utils.flood_protect import FloodProtector

flood_protector = FloodProtector()

async def findproduct_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not flood_protector.is_allowed(user_id):
        await update.message.reply_text("You're sending commands too fast. Slow down.")
        return
    # your existing findproduct logic here
