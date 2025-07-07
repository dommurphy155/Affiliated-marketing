import os
import asyncio
import logging
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import openai
from playwright.async_api import async_playwright

# Load env
load_dotenv()
REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "OPENAI_API_KEY",
    "CLICKBANK_NICKNAME", "TIKTOK_EMAIL", "TIKTOK_PASSWORD",
    "CAPCUT_EMAIL", "CAPCUT_PASSWORD"
]
MISSING_VARS = [v for v in REQUIRED_VARS if not os.getenv(v)]
if MISSING_VARS:
    raise RuntimeError(f"Missing env vars: {MISSING_VARS}")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLICKBANK_NICKNAME = os.getenv("CLICKBANK_NICKNAME")
TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
CAPCUT_EMAIL = os.getenv("CAPCUT_EMAIL")
CAPCUT_PASSWORD = os.getenv("CAPCUT_PASSWORD")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_PATH = "affiliate_bot.db"
SCRAPE_INTERVAL = 6 * 3600  # 6 hours

# DB Setup
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            name TEXT,
            category TEXT,
            price TEXT,
            commission_pct REAL,
            estimated_sales INTEGER,
            description TEXT,
            platform TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT,
            amount REAL,
            commission_pct REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            platform TEXT
        )''')
        conn.commit()

init_db()

class DBManager:
    @staticmethod
    def add_product(p):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO products (url,name,category,price,commission_pct,estimated_sales,description,platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p['url'], p['name'], p['category'], p['price'],
                p.get('commission_pct', 0), p.get('estimated_sales', 0),
                p['description'], p.get('platform', 'unknown')
            ))

    @staticmethod
    def get_pending_products(limit=3):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''SELECT * FROM products WHERE status="pending"
                         ORDER BY commission_pct DESC LIMIT ?''', (limit,))
            rows = c.fetchall()
            keys = [col[0] for col in c.description]
            return [dict(zip(keys, r)) for r in rows]

    @staticmethod
    def update_product_status(url, status):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('UPDATE products SET status=? WHERE url=?', (status, url))

class Scraper:
    @staticmethod
    async def scrape_clickbank():
        logging.info("Scraping ClickBank...")
        results = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://marketplace.clickbank.com/")
                await page.wait_for_timeout(2000)
                cards = await page.query_selector_all('[data-testid="product-card"]')
                for card in cards[:5]:
                    try:
                        title = await card.query_selector_eval('h3', 'el => el.textContent')
                        gravity = await card.query_selector_eval('[data-testid="gravity"]', 'el => el.textContent')
                        commission = await card.query_selector_eval('[data-testid="commission"]', 'el => el.textContent')
                        gravity = float(''.join(filter(str.isdigit, gravity))) or 0
                        commission = float(''.join(filter(lambda x: x.isdigit() or x=='.', commission))) or 0
                        if gravity >= 30 and commission >= 15:
                            results.append({
                                "url": f"https://clickbank.com/{hash(title)}",
                                "name": title.strip(),
                                "category": "Digital",
                                "price": "Varies",
                                "commission_pct": commission,
                                "estimated_sales": int(gravity * 15),
                                "description": "Top trending ClickBank offer",
                                "platform": "ClickBank"
                            })
                    except Exception as e:
                        logging.warning(f"ClickBank card error: {e}")
                await browser.close()
        except Exception as e:
            logging.error(f"ClickBank scrape failed: {e}")
        return results

class AffiliateBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        self.last_scrape_time = 0
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("findproduct", self.cmd_findproduct))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("money glitch is printing ✅\n\nAll systems green.")

    async def cmd_findproduct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = time.time()
        if now - self.last_scrape_time < SCRAPE_INTERVAL:
            remaining = int((SCRAPE_INTERVAL - (now - self.last_scrape_time)) / 60)
            await update.message.reply_text(f"⏳ Please wait {remaining} minutes.")
            return

        await update.message.reply_text("🔍 Scraping products...")
        products = await Scraper.scrape_clickbank()
        db = DBManager()
        for p in products:
            db.add_product(p)

        self.last_scrape_time = now
        pending = db.get_pending_products()
        if not pending:
            await update.message.reply_text("❌ No eligible products found.")
            return

        for product in pending:
            await self.send_approval(update, product)

    async def send_approval(self, update, product):
        link = f"{product['url']}?tid={CLICKBANK_NICKNAME}"
        text = (
            f"🔥 Product: {product['name']}\n"
            f"💰 Commission: {product['commission_pct']}%\n"
            f"📈 Est. Sales: {product['estimated_sales']}\n"
            f"🛍️ Category: {product['category']}\n"
            f"🔗 {link}"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve|{product['url']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject|{product['url']}")
            ]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        action, url = query.data.split("|")
        DBManager.update_product_status(url, "approved" if action == "approve" else "rejected")
        await query.edit_message_text(f"✅ Product {action}d.")

    def run(self):
        self.app.run_polling()

if __name__ == "__main__":
    try:
        AffiliateBot().run()
    except Exception as e:
        logging.exception("❌ Bot crashed")
        Bot(token=TELEGRAM_BOT_TOKEN).send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ Bot crashed:\n{e}")
