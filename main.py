import asyncio
import logging
import signal
import sys
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Defaults,
    PicklePersistence,
)

from scraper import scrape_clickbank_top_offers
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
        rf"Hi {user.mention_html()}! Bot is running 🚀", quote=True
    )
    logger.info(f"/start command triggered by user {user.id}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Stopping bot gracefully...")
    logger.info(f"/stop command triggered by user {user.id}")
    await context.application.stop()
    await context.application.shutdown()
    shutdown_event.set()


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # You can expand with actual status info later
    await update.message.reply_text("Bot is online and operational.")


async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Starting product scraping...")
    logger.info("Product scraping started by user command")
    try:
        products = await asyncio.to_thread(scrape_clickbank_top_offers)
        if not products:
            await update.message.reply_text("No products found.")
            return

        msg = "Top ClickBank offers:\n"
        for p in products[:10]:
            # Expected product dict keys: name, price, commission, url, etc.
            msg += (
                f"- {p['name']} | Price: {p['price']} | Commission: {p['commission']}\n"
                f"  {p['url']}\n"
            )
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error in find_product: {e}", exc_info=True)
        await update.message.reply_text("Error occurred during scraping.")


async def postvideo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Starting video posting...")
    logger.info("Video posting started by user command")
    try:
        result = await post_video()
        await update.message.reply_text(f"Video posted successfully: {result}")
    except Exception as e:
        logger.error(f"Error in postvideo: {e}", exc_info=True)
        await update.message.reply_text("Error occurred during video posting.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "/start - Start the bot\n"
        "/stop - Stop the bot\n"
        "/status - Get current status\n"
        "/findproduct - Scrape and list top products\n"
        "/postvideo - Post a product video on TikTok\n"
        "/help - Show this help message\n"
        "/dailyreport - Show today's sales report\n"
        "/weeklyreport - Show this week's sales report\n"
        "/resetstats - Reset performance stats\n"
    )
    await update.message.reply_text(help_text)
    logger.info(f"/help command triggered by user {update.effective_user.id}")


async def dailyreport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder - integrate your daily report logic here
    await update.message.reply_text("Daily report: Not implemented yet.")


async def weeklyreport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder - integrate your weekly report logic here
    await update.message.reply_text("Weekly report: Not implemented yet.")


async def resetstats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder - implement stats reset logic if needed
    await update.message.reply_text("Stats reset: Not implemented yet.")


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
    app.add_handler(CommandHandler("dailyreport", dailyreport))
    app.add_handler(CommandHandler("weeklyreport", weeklyreport))
    app.add_handler(CommandHandler("resetstats", resetstats))

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
