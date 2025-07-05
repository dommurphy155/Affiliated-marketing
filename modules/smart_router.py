from telegram import Update
from telegram.ext import ContextTypes
import logging

async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "⚠️ Unknown command.\n\n"
        "Try one of these:\n"
        "/findproduct — Find new high-converting product\n"
        "/postvideo — Post TikTok for current product\n"
        "/products — List active products\n"
        "/daily — Show today’s earnings\n"
        "/weekly — Show 7-day earnings\n"
        "/status — Check system status"
    )
    await update.message.reply_text(msg)
