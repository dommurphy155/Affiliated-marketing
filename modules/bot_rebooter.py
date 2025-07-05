from telegram import Update
from telegram.ext import ContextTypes

async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Restart command placeholder - no action taken.')
