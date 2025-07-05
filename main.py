import os
import json
import asyncio
import logging
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

load_dotenv()  # Load .env values

logging.basicConfig(level=logging.INFO)

PRODUCTS_FILE = "products.json"
EARNINGS_FILE = "earnings.json"

# Load and save helpers
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Load DBs on startup
products_db = load_json(PRODUCTS_FILE, [])
earnings_db = load_json(EARNINGS_FILE, {"daily": 0, "weekly": 0})

async def scrape_viral_product():
    logging.info("Starting scrape of AliExpress trending products.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.aliexpress.com/category/200003482/trending-products.html"
        await page.goto(url)
        await page.wait_for_selector('.manhattan--titleText--WccSj')

        product_name = await page.locator('.manhattan--titleText--WccSj').first.inner_text()
        image_url = await page.locator('.manhattan--imgContainer--1lP57 img').first.get_attribute('src')

        logging.info(f"Scraped product: {product_name} | Image URL: {image_url}")

        # Download product image
        screenshot_path = f"product_{int(datetime.now().timestamp())}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    with open(screenshot_path, 'wb') as f:
                        f.write(await resp.read())
                else:
                    logging.warning(f"Failed to download image, status: {resp.status}")
                    screenshot_path = None

        await browser.close()

    potential_earnings = "£100/day (estimate)"  # Static for now

    product = {
        "id": len(products_db) + 1,
        "name": product_name,
        "screenshot_path": screenshot_path,
        "potential_earnings": potential_earnings,
        "timestamp": datetime.utcnow().isoformat(),
    }
    products_db.append(product)
    save_json(PRODUCTS_FILE, products_db)

    return product

async def post_video_to_tiktok(product):
    username = os.getenv("TIKTOK_EMAIL")
    password = os.getenv("TIKTOK_PASSWORD")
    video_path = os.getenv("VIDEO_PATH")  # Must be set and file must exist

    if not video_path or not os.path.exists(video_path):
        logging.error("Video file path not set or file does not exist. Aborting TikTok post.")
        return False

    logging.info(f"Starting TikTok posting for product: {product['name']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://www.tiktok.com/login")
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            logging.error(f"Login failed: {e}")
            await browser.close()
            return False

        try:
            await page.goto("https://www.tiktok.com/upload")
            await page.wait_for_selector('input[type="file"]', timeout=10000)
            await page.set_input_files('input[type="file"]', video_path)
            await asyncio.sleep(5)
            await page.click('button[data-e2e="upload-post-button"]')
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Failed to upload or post video: {e}")
            await browser.close()
            return False

        await browser.close()

    logging.info("Video posted successfully on TikTok.")
    return True

# Telegram command handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Commands available:\n"
        "/findproduct - Find new viral product\n"
        "/postvideo - Post new video about product\n"
        "/products - List saved products\n"
        "/daily - Show daily earnings\n"
        "/weekly - Show weekly earnings\n"
        "/status - Show bot status"
    )

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Finding viral product, please wait...")
    try:
        product = await scrape_viral_product()
        if product["screenshot_path"]:
            with open(product["screenshot_path"], "rb") as img:
                await update.message.reply_photo(
                    img,
                    caption=f"{product['name']}\nPotential earnings: {product['potential_earnings']}"
                )
        else:
            await update.message.reply_text(f"{product['name']}\nPotential earnings: {product['potential_earnings']}\nNo image available.")
    except Exception as e:
        logging.error(f"Error in find_product: {e}")
        await update.message.reply_text("Failed to find product, try again later.")

async def post_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products_db:
        await update.message.reply_text("No products available to post video for.")
        return
    product = products_db[-1]  # Post latest product
    await update.message.reply_text(f"Posting video for product: {product['name']}")
    success = await post_video_to_tiktok(product)
    if success:
        await update.message.reply_text("Posted video successfully.")
    else:
        await update.message.reply_text("Failed to post video.")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products_db:
        await update.message.reply_text("No products saved yet.")
        return
    reply = "Saved products:\n"
    for p in products_db:
        reply += f"{p['id']}. {p['name']} - Earnings: {p['potential_earnings']}\n"
    await update.message.reply_text(reply)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Daily earnings: £{earnings_db.get('daily', 0)}")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Weekly earnings: £{earnings_db.get('weekly', 0)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running and ready.")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", post_video))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("status", status))

    logging.info("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
