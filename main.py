import asyncio
import logging
import os
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is live and working.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to get going.")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Telegram Bot Token missing from environment variables.")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("🤖 Bot started. Running...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
