import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load .env credentials
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Telegram command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running.")

# Telegram command: /findproduct
async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Finding a viral product... (placeholder)")

# Telegram command: /postvideo
async def post_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📹 Posting video to all platforms... (placeholder)")

# Telegram command: /products
async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛒 Listing saved products... (placeholder)")

# Telegram command: /daily
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Daily earnings: £0.00 (placeholder)")

# Telegram command: /weekly
async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Weekly earnings: £0.00 (placeholder)")

# Telegram command: /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📡 Status: Bot is operational.")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", post_video))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("status", status))

    logging.info("✅ Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

Do I have to add this to my console as well of github?
