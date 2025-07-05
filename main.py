import os, logging, nest_asyncio, asyncio
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters
)
from telegram import Update
from modules.product_finder import handle as findproduct_handler
from modules.video_poster import handle as postvideo_handler
from modules.earnings_tracker import handle_daily, handle_weekly
from modules.status_checker import handle_status
from modules.product_list import handle_products
from modules.smart_router import unknown_command_handler

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("Bot token missing")
        return

    try:
        app = ApplicationBuilder().token(token).build()

        app.add_handler(CommandHandler("start", handle_status))
        app.add_handler(CommandHandler("status", handle_status))
        app.add_handler(CommandHandler("findproduct", findproduct_handler))
        app.add_handler(CommandHandler("postvideo", postvideo_handler))
        app.add_handler(CommandHandler("daily", handle_daily))
        app.add_handler(CommandHandler("weekly", handle_weekly))
        app.add_handler(CommandHandler("products", handle_products))

        app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

        logging.info("Bot started and polling...")
        await app.run_polling()

    except Exception as e:
        logging.error(f"Bot failed to start: {e}")

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
