from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import os
import logging
import nest_asyncio
from dotenv import load_dotenv
import asyncio
import sys
import traceback
import signal

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")  # optional ping

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Import async handlers
from modules.product_finder import handle as findproduct_handler
from modules.video_poster import handle as postvideo_handler
from modules.earnings_tracker import handle_daily, handle_weekly
from modules.status_checker import handle_status
from modules.product_list import handle_products
from modules.uptime_checker import handle_uptime
from modules.memory_checker import handle_memory
from modules.bot_killer import handle_kill
from modules.bot_rebooter import handle_restart
from modules.log_reporter import handle_log

# Basic /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online and ready.")

# Graceful shutdown handler
def handle_shutdown():
    logging.info("Shutdown signal received. Cleaning up...")
    sys.exit(0)

# Optional watchdog / heartbeat
async def heartbeat():
    while True:
        if HEALTHCHECK_URL:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    await session.get(HEALTHCHECK_URL)
                logging.info("Sent healthcheck ping.")
            except Exception as e:
                logging.warning(f"Healthcheck failed: {e}")
        await asyncio.sleep(3600)  # hourly

# Main runner
async def main():
    try:
        if not TELEGRAM_TOKEN:
            logging.error("TELEGRAM_BOT_TOKEN is not set in .env")
            sys.exit(1)

        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Register handlers with audit log
        commands = [
            ("start", start),
            ("findproduct", findproduct_handler),
            ("postvideo", postvideo_handler),
            ("daily", handle_daily),
            ("weekly", handle_weekly),
            ("status", handle_status),
            ("products", handle_products),
            ("uptime", handle_uptime),
            ("memory", handle_memory),
            ("kill", handle_kill),
            ("restart", handle_restart),
            ("log", handle_log),
        ]

        for name, func in commands:
            app.add_handler(CommandHandler(name, func))
            logging.info(f"Registered command: /{name}")

        logging.info("Bot polling started.")

        # Add shutdown hooks
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_shutdown)

        # Start optional heartbeat in background
        if HEALTHCHECK_URL:
            loop.create_task(heartbeat())

        await app.run_polling()

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

# Entry point
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
