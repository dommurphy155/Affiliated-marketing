import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running.")

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Finding a viral product... (placeholder)")

async def post_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Posting video to all platforms... (placeholder)")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Listing saved products... (placeholder)")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Daily earnings: £0.00 (placeholder)")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Weekly earnings: £0.00 (placeholder)")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Status: Bot is operational.")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN is not set in environment variables. Exiting.")
        return

    try:
        app = ApplicationBuilder().token(token).build()

        # Register command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("findproduct", find_product))
        app.add_handler(CommandHandler("postvideo", post_video))
        app.add_handler(CommandHandler("products", products))
        app.add_handler(CommandHandler("daily", daily))
        app.add_handler(CommandHandler("weekly", weekly))
        app.add_handler(CommandHandler("status", status))

        logging.info("Bot started and running...")
        # Run polling without closing the loop to avoid RuntimeError
        await app.run_polling()
    except Exception as e:
        logging.error(f"Exception in main: {e}", exc_info=True)

if __name__ == "__main__":
    import nest_asyncio

    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
