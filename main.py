import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (make sure you have python-dotenv installed and .env file configured)
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Example command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot started. Ready to roll.")

async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram Bot Token not found in environment variables!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers here
    app.add_handler(CommandHandler("start", start))

    logger.info("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
