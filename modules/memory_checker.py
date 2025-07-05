from telegram import Update
from telegram.ext import ContextTypes

async def handle_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Memory check feature is not implemented yet.')
