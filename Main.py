import os
from datetime import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
    await context.bot.send_message(chat_id=chat_id, text="✅ Daily report running...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is online and ready.")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    application = ApplicationBuilder().token(token).build()

    # Add /start command
    application.add_handler(CommandHandler("start", start))

    async def on_startup(app):
        # Schedule the daily report after bot is initialized
        app.job_queue.run_daily(daily_report, time=time(hour=9, minute=0))

    application.post_init = on_startup

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
