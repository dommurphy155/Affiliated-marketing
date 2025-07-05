import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Import your async handlers here, ensure they are async def
from modules.product_finder import handle as findproduct_handler
from modules.video_poster import handle as postvideo_handler
from modules.earnings_tracker import handle_daily, handle_weekly
from modules.status_checker import handle_status

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started.")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN is not set in environment")
        return

    app = ApplicationBuilder().token(token).build()

    # Register your command handlers here
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("findproduct", findproduct_handler))
    app.add_handler(CommandHandler("postvideo", postvideo_handler))
    app.add_handler(CommandHandler("daily", handle_daily))
    app.add_handler(CommandHandler("weekly", handle_weekly))
    app.add_handler(CommandHandler("status", handle_status))

    logging.info("Bot started and running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
