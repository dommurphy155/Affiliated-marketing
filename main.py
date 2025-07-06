import asyncio
import logging
import signal
import sys
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Defaults, PicklePersistence, Application

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable not set. Exiting.")
    sys.exit(1)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_data.pkl")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(rf"Hi {user.mention_html()}! Bot is running 🚀", quote=True)
    logger.info(f"/start command triggered by user {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "/start - Start the bot\n/help - Show this help message"
    await update.message.reply_text(help_text)
    logger.info(f"/help command triggered by user {update.effective_user.id}")

shutdown_event = asyncio.Event()

def shutdown_signal_handler(signum, frame):
    logger.info(f"Received shutdown signal: {signum}, shutting down gracefully...")
    shutdown_event.set()

async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_signal_handler, sig, None)

    app: Application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .persistence(persistence) \
        .defaults(Defaults(parse_mode="HTML")) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await shutdown_event.wait()

    await app.updater.stop_polling()
    await app.stop()
    await app.shutdown()
    logger.info("Bot stopped cleanly. Exiting.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
