import json
import asyncio
import logging
import aiohttp
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from video_generator import create_video
from dotenv import load_dotenv
import nest_asyncio

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

PRODUCTS_FILE = "products.json"
EARNINGS_FILE = "earnings.json"

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

products_db = load_json(PRODUCTS_FILE, [])
earnings_db = load_json(EARNINGS_FILE, {"daily": 0, "weekly": 0})

async def scrape_viral_product():
    logging.info("Scraping AliExpress for trending product.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.aliexpress.com/category/200003482/trending-products.html")
        await page.wait_for_selector('.manhattan--titleText--WccSj')

        product_name = await page.locator('.manhattan--titleText--WccSj').first.inner_text()
        image_url = await page.locator('.manhattan--imgContainer--1lP57 img').first.get_attribute('src')
        screenshot_path = f"autoposts/product_{int(datetime.now().timestamp())}.jpg"

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    os.makedirs("autoposts", exist_ok=True)
                    with open(screenshot_path, 'wb') as f:
                        f.write(await resp.read())
                else:
                    logging.warning("Failed to download image.")
                    screenshot_path = None

        await browser.close()

    potential_earnings = "£100/day (est.)"
    product = {
        "id": len(products_db) + 1,
        "name": product_name,
        "screenshot_path": screenshot_path,
        "potential_earnings": potential_earnings,
        "timestamp": datetime.utcnow().isoformat()
    }

    video_path = await asyncio.to_thread(create_video, product_name, screenshot_path)
    product["video_path"] = video_path if video_path else None

    products_db.append(product)
    save_json(PRODUCTS_FILE, products_db)
    return product

async def post_video_to_tiktok(product):
    username = os.getenv("TIKTOK_EMAIL")
    password = os.getenv("TIKTOK_PASSWORD")
    video_path = product.get("video_path")

    if not video_path or not os.path.exists(video_path):
        logging.error("No video found to post.")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login")

        try:
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            logging.error(f"TikTok login failed: {e}")
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
            logging.error(f"Post failed: {e}")
            await browser.close()
            return False

        await browser.close()
    return True

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/findproduct - Scrape viral product\n"
        "/postvideo - Upload video\n"
        "/products - List products\n"
        "/daily - Daily earnings\n"
        "/weekly - Weekly earnings\n"
        "/status - Bot status"
    )

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scraping product...")
    try:
        product = await scrape_viral_product()
        if product.get("screenshot_path"):
            with open(product["screenshot_path"], "rb") as img:
                await update.message.reply_photo(
                    img, caption=f"{product['name']}\nEarnings: {product['potential_earnings']}"
                )
        else:
            await update.message.reply_text(f"{product['name']}\nNo image.")
    except Exception as e:
        logging.error(f"Scrape error: {e}")
        await update.message.reply_text("Failed to find product.")

async def post_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products_db:
        await update.message.reply_text("No products yet.")
        return
    product = products_db[-1]
    await update.message.reply_text(f"Posting: {product['name']}")
    if await post_video_to_tiktok(product):
        await update.message.reply_text("Posted.")
    else:
        await update.message.reply_text("Post failed.")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products_db:
        await update.message.reply_text("No products saved.")
        return
    reply = "\n".join(f"{p['id']}. {p['name']} - {p['potential_earnings']}" for p in products_db)
    await update.message.reply_text(reply)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Daily: £{earnings_db.get('daily', 0)}")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Weekly: £{earnings_db.get('weekly', 0)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running.")

async def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", post_video))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("status", status))

    logging.info("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
