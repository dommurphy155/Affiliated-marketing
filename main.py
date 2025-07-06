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

# Import your existing scraper and poster modules
from scraper import find_products  # async def find_products()
from poster import post_video      # async def post_video(product)
from daily_report import send_daily_report  # async def send_daily_report(context)
from daily_report import send_weekly_report  # async def send_weekly_report(context)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN env var not set. Exiting.")
    sys.exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="bot_data.pkl")
shutdown_event = asyncio.Event()

def shutdown_signal_handler(signum, frame):
    logger.info(f"Received shutdown signal: {signum}, shutting down gracefully...")
    shutdown_event.set()

# Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Bot is running 🚀",
        quote=True,
    )
    logger.info(f"/start by user {user.id}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Bot shutting down gracefully.")
    logger.info(f"/stop by user {user.id}")
    shutdown_event.set()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Add your custom status info here
    status_msg = "Bot is running.\n"
    status_msg += f"Active users: {len(context.application.persistence.user_data)}\n"
    await update.message.reply_text(status_msg)
    logger.info(f"/status by user {update.effective_user.id}")

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Finding best products, please wait...")
    logger.info(f"/findproduct triggered by user {user.id}")
    try:
        products = await find_products()  # Your scraper async func returns list/dict of products
        if not products:
            await update.message.reply_text("No products found. Try again later.")
            return
        # Format top 10 products info nicely
        text = "Top 10 Products:\n"
        for i, p in enumerate(products[:10], 1):
            text += f"{i}. {p['name']} - ${p['price']} - Commission: {p['commission']}%\n"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Error in find_product: {e}", exc_info=True)
        await update.message.reply_text("Error finding products. Try again later.")

async def postvideo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Posting video to TikTok and others...")
    logger.info(f"/postvideo triggered by user {user.id}")
    try:
        # Example: post top product or product id passed as argument
        product = None
        if context.args:
            product_id = context.args[0]
            # Fetch product by id from your DB or cache - stub here:
            product = {"id": product_id, "name": "Sample Product"}
        else:
            # fallback to last found or best product - stub here:
            product = {"id": "123", "name": "Sample Product"}
        await post_video(product)
        await update.message.reply_text(f"Video posted for product: {product['name']}")
    except Exception as e:
        logger.error(f"Error in postvideo: {e}", exc_info=True)
        await update.message.reply_text("Failed to post video.")

async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Generating daily report...")
    logger.info(f"/dailyreport triggered by user {user.id}")
    try:
        await send_daily_report(context)
        await update.message.reply_text("Daily report sent.")
    except Exception as e:
        logger.error(f"Error in daily_report: {e}", exc_info=True)
        await update.message.reply_text("Failed to send daily report.")

async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text("Generating weekly report...")
    logger.info(f"/weeklyreport triggered by user {user.id}")
    try:
        await send_weekly_report(context)
        await update.message.reply_text("Weekly report sent.")
    except Exception as e:
        logger.error(f"Error in weekly_report: {e}", exc_info=True)
        await update.message.reply_text("Failed to send weekly report.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "/start - Start bot\n"
        "/stop - Stop bot\n"
        "/status - Get bot status\n"
        "/findproduct - Find top products\n"
        "/postvideo [product_id] - Post video of product\n"
        "/dailyreport - Get daily earnings report\n"
        "/weeklyreport - Get weekly earnings report\n"
        "/help - Show this help\n"
    )
    await update.message.reply_text(help_text)
    logger.info(f"/help command triggered by user {update.effective_user.id}")

async def main() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_signal_handler, sig, None)

    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .persistence(persistence) \
        .defaults(Defaults(parse_mode="HTML")) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", postvideo))
    app.add_handler(CommandHandler("dailyreport", daily_report))
    app.add_handler(CommandHandler("weeklyreport", weekly_report))
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
