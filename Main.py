import os
from datetime import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
    print("Running daily_report")  # Debug print
    await context.bot.send_message(chat_id=chat_id, text="✅ Daily report running...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received /start command")  # Debug print
    await update.message.reply_text("🤖 Bot is online and ready.")

def main():
    print("Starting main()")  # Debug print
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    application = ApplicationBuilder().token(token).build()
    print("Application built")  # Debug print

    application.add_handler(CommandHandler("start", start))

    async def on_startup(app):
        print("Running on_startup")  # Debug print
        app.job_queue.run_daily(daily_report, time=time(hour=9, minute=0))

    application.post_init = on_startup

    print("Starting polling")  # Debug print
    application.run_polling()
    print("Polling ended")  # Won't normally hit this unless bot stops

if __name__ == "__main__":
    main()
