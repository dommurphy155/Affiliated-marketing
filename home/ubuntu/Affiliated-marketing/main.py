import asyncio
import logging
import signal
import sys
import os

from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Defaults,
    PicklePersistence,
)

from scraper import scrape_all
from poster import post_video

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLICKBANK_NICKNAME = os.getenv("CLICKBANK_NICKNAME")
TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN env var not set. Exiting.")
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_data.pkl")
shutdown_event = asyncio.Event()


def shutdown_signal_handler(signum, frame):
    logger.info(f"Received shutdown signal: {signum}, shutting down gracefully...")
    shutdown_event.set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Bot is running.", quote=True
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Stopping bot.")
    await context.application.stop()
    await context.application.shutdown()
    shutdown_event.set()


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot is live and operational.")


async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Scraping products...")
    try:
        products = await asyncio.to_thread(scrape_all)
        if not products:
            await update.message.reply_text("No products found.")
            return

        msg = "Top Products:\n"
        for p in products[:10]:
            msg += (
                f"- {p['name']} | Price: {p['price']} | Commission: {p['commission']}\n"
                f"  {p['url']}\n"
            )
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error in find_product: {e}", exc_info=True)
        await update.message.reply_text("Scraping failed.")


async def postvideo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Generating and posting TikTok video...")
    try:
        result = await post_video()
        await update.message.reply_text(f"Posted: {result}")
    except Exception as e:
        logger.error(f"Error in postvideo: {e}", exc_info=True)
        await update.message.reply_text("Video post failed.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "/start - Start the bot\n"
        "/stop - Stop the bot\n"
        "/status - Bot status\n"
        "/findproduct - Scrape top products\n"
        "/postvideo - Generate and post video\n"
        "/help - Show commands\n"
    )
    await update.message.reply_text(help_text)


async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_signal_handler, sig, None)

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .defaults(Defaults(parse_mode="HTML"))
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", postvideo))
    app.add_handler(CommandHandler("help", help_command))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await shutdown_event.wait()
    await app.updater.stop_polling()
    await app.stop()
    await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
