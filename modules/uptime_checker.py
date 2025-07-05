from telegram import Update
from telegram.ext import ContextTypes

async def handle_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Uptime check feature is not implemented yet.')
