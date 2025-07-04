import os
from datetime import time
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
    await context.bot.send_message(chat_id=chat_id, text="Daily report running...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started and ready.")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    application = ApplicationBuilder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # Schedule daily_report to run every day at 9:00 AM UTC (adjust time as needed)
    job_queue = application.job_queue
    job_queue.run_daily(daily_report, time=time(hour=9, minute=0, second=0))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
