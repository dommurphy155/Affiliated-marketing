import os
import json
import asyncio
import logging
from datetime import datetime
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Replace URL with real viral product marketplace URL
        await page.goto("https://viralproducts.example.com/trending")

        # Scrape product name and screenshot product image
        product_name = await page.locator(".product-title").inner_text()
        screenshot_path = f"product_{int(datetime.now().timestamp())}.png"
        await page.locator(".product-image").screenshot(path=screenshot_path)

        await browser.close()

    # Dummy earnings calc, replace with your logic
    potential_earnings = "£100/day"

    product = {
        "id": len(products_db) + 1,
        "name": product_name,
        "screenshot_path": screenshot_path,
        "potential_earnings": potential_earnings,
    }
    products_db.append(product)
    save_json(PRODUCTS_FILE, products_db)

    return product

async def post_video_to_platforms(product):
    username = os.getenv("TIKTOK_USERNAME")
    password = os.getenv("TIKTOK_PASSWORD")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Login to TikTok
        await page.goto("https://www.tiktok.com/login")
        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # Navigate to upload (change URL to actual)
        await page.goto("https://www.tiktok.com/upload")

        # Upload video placeholder: adapt to real UI
        # await page.set_input_files('input[type="file"]', product["video_path"])

        # await page.click('button.post-submit')

        await asyncio.sleep(5)  # wait for upload
        await browser.close()

    return True

# Telegram commands

async def find_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Finding viral product, please wait...")
    product = await scrape_viral_product()
    with open(product["screenshot_path"], "rb") as img:
        await update.message.reply_photo(img,
                                         caption=f"{product['name']}\nPotential earnings: {product['potential_earnings']}")

async def post_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not products_db:
        await update.message.reply_text("No products available to post video for.")
        return
    product = products_db[-1]  # Post latest product
    await update.message.reply_text(f"Posting video for product: {product['name']}")
    success = await post_video_to_platforms(product)
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
    await update.message.reply_text(f"Daily earnings: £{earnings_db['daily']}")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Weekly earnings: £{earnings_db['weekly']}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running and ready.")

# Setup Telegram bot

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("findproduct", find_product))
    app.add_handler(CommandHandler("postvideo", post_video))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("status", status))

    print("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
