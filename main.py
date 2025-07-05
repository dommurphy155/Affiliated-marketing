import asyncio
import nest_asyncio
nest_asyncio.apply()

from telegram.ext import ApplicationBuilder
import logging
from video_generator import create_video
from content_generator import generate_content
from autopost import post_to_socials
from scraper import scrape_product
from telemetry import log_event
from affiliate_engine import get_affiliate_link

logging.basicConfig(level=logging.INFO)

async def main():
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Your bot handlers setup here
    # e.g., app.add_handler(...)

    logging.info("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
