import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from datetime import datetime

# Load from .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

# Launch Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="💸 Money printer is ON!"
    )

# Echo Handler (Basic test command)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You said: {update.message.text}"
    )

# Daily Stats Sender (Placeholder version — hook this up to actual revenue later)
async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats_message = (
        f"📈 Daily Stats Report — {now}\n"
        f"• Total clicks: 192\n"
        f"• Leads captured: 31\n"
        f"• Estimated revenue: £58.23\n"
        f"• Top product: Viral Digital Course #3\n"
        f"• Conversion rate: 16.1%"
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=stats_message)

# Main Entry
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Job Queue: send stats once every 24h
    job_queue = app.job_queue
    job_queue.run_repeating(send_daily_stats, interval=86400, first=5)

    print("🚀 Money printer bot is running…")
    app.run_polling()
