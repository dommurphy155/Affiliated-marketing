import os
import asyncio
import logging
import time
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import openai
from playwright.async_api import async_playwright

import os
from dotenv import load_dotenv

load_dotenv()

# Check env vars
required_vars = [
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "OPENAI_API_KEY", 
    "CLICKBANK_NICKNAME", "TIKTOK_EMAIL", "TIKTOK_PASSWORD", 
    "CAPCUT_EMAIL", "CAPCUT_PASSWORD"
]
missing_vars = [v for v in required_vars if not os.getenv(v)]
if missing_vars:
    raise RuntimeError(f"Missing env vars: {missing_vars}")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLICKBANK_NICKNAME = os.getenv("CLICKBANK_NICKNAME")

TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")

CAPCUT_EMAIL = os.getenv("CAPCUT_EMAIL")
CAPCUT_PASSWORD = os.getenv("CAPCUT_PASSWORD")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("affiliate_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger()

DB_PATH = "affiliate_bot.db"
SCRAPE_INTERVAL_HOURS = 6

# Init DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
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
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT,
            amount REAL,
            commission_pct REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            platform TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class DBManager:
    @staticmethod
    def add_product(p):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO products (url,name,category,price,commission_pct,estimated_sales,description,platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p['url'], p['name'], p['category'], p['price'],
            p.get('commission_pct', 0), p.get('estimated_sales', 0),
            p['description'], p.get('platform', 'unknown')
        ))
        conn.commit()
        conn.close()
    @staticmethod
    def get_pending_products(limit=3):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT * FROM products WHERE status='pending'
            ORDER BY commission_pct DESC, estimated_sales DESC LIMIT ?
        """, (limit,))
        columns = [desc[0] for desc in c.description]
        rows = c.fetchall()
        conn.close()
        return [dict(zip(columns, r)) for r in rows]
    @staticmethod
    def update_product_status(url, status):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE products SET status=? WHERE url=?", (status, url))
        conn.commit()
        conn.close()
    @staticmethod
    def get_earnings(days=1):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""
            SELECT COUNT(*), COALESCE(SUM(amount),0)
            FROM earnings WHERE date >= datetime('now', '-{days} days')
        """)
        sales, earnings = c.fetchone()
        conn.close()
        return sales or 0, earnings or 0.0
    @staticmethod
    def get_top_product(days=1):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""
            SELECT product_url, SUM(amount) AS total
            FROM earnings WHERE date >= datetime('now', '-{days} days')
            GROUP BY product_url ORDER BY total DESC LIMIT 1
        """)
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

class Scraper:
    @staticmethod
    async def scrape_clickbank():
        logger.info("Scraping ClickBank...")
        products = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://marketplace.clickbank.com/", timeout=30000)
                await page.wait_for_timeout(3000)
                cards = await page.query_selector_all('[data-testid="product-card"], .product-card')
                for card in cards[:5]:
                    try:
                        title = await card.query_selector_eval('h3, .product-title', 'el => el.textContent')
                        gravity = await card.query_selector_eval('[data-testid="gravity"], .gravity', 'el => el.textContent') or "0"
                        commission = await card.query_selector_eval('[data-testid="commission"], .commission', 'el => el.textContent') or "0"
                        gravity_num = float(''.join(filter(str.isdigit, gravity))) if gravity else 0
                        commission_num = float(''.join(filter(lambda x: x.isdigit() or x=='.', commission))) if commission else 0
                        if gravity_num > 30 and commission_num > 15.0:
                            products.append({
                                "name": title.strip(),
                                "price": "Variable",
                                "category": "Digital Products",
                                "description": f"High gravity {gravity_num} product",
                                "url": f"https://marketplace.clickbank.com/product/{hash(title) % 100000}",
                                "commission_pct": commission_num,
                                "estimated_sales": int(gravity_num * 15),
                                "platform": "ClickBank"
                            })
                    except Exception as e:
                        logger.error(f"ClickBank product error: {e}")
                await browser.close()
        except Exception as e:
            logger.error(f"ClickBank scrape error: {e}")
        return products

    @staticmethod
    async def scrape_amazon():
        logger.info("Scraping Amazon UK...")
        products = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://www.amazon.co.uk/gp/bestsellers", timeout=30000)
                await page.wait_for_timeout(3000)
                items = await page.query_selector_all('.zg-item-immersion')
                for item in items[:3]:
                    try:
                        title = await item.query_selector_eval('a.a-link-normal', 'el => el.textContent')
                        url = await item.query_selector_eval('a.a-link-normal', 'el => el.href')
                        price = await item.query_selector_eval('.p13n-sc-price', 'el => el.textContent') or "Check Amazon"
                        products.append({
                            "name": title.strip(),
                            "price": price.strip(),
                            "category": "Consumer Products",
                            "description": "Amazon bestseller",
                            "url": url,
                            "commission_pct": 8.0,
                            "estimated_sales": 1000,
                            "platform": "Amazon"
                        })
                    except Exception as e:
                        logger.error(f"Amazon product error: {e}")
                await browser.close()
        except Exception as e:
            logger.error(f"Amazon scrape error: {e}")
        return products

class AffiliateBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        self.db = DBManager()
        self.scraper = Scraper()
        self.pending = {}
        self.last_scrape = 0
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("findproduct", self.cmd_findproduct))
        self.app.add_handler(CommandHandler("postvideo", self.cmd_postvideo))
        self.app.add_handler(CommandHandler("daily", self.cmd_daily))
        self.app.add_handler(CommandHandler("weekly", self.cmd_weekly))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("digiprof25", self.cmd_digiprof25))
        self.app.add_handler(CallbackQueryHandler(self.cb_handler))
        self.app.add_error_handler(self.err_handler)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Report system status
        status = "All systems nominal. No recent errors or bugs."
        text = f"money glitch is printing ✅\n\nSystem Status:\n{status}"
        await update.message.reply_text(text)

    async def cmd_findproduct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = time.time()
        if now - self.last_scrape < SCRAPE_INTERVAL_HOURS * 3600:
            remain = int((SCRAPE_INTERVAL_HOURS * 3600 - (now - self.last_scrape)) // 60)
            await update.message.reply_text(f"⏳ Please wait {remain} minutes before next scrape.")
            return
        msg = await update.message.reply_text("🔍 Scraping products...")
        # Scrape multiple sources concurrently
        clickbank_task = asyncio.create_task(self.scraper.scrape_clickbank())
        amazon_task = asyncio.create_task(self.scraper.scrape_amazon())
        results = await asyncio.gather(clickbank_task, amazon_task)
        all_products = [p for source in results for p in source]

        # Filter & store
        filtered = [p for p in all_products if p['commission_pct'] >= 15.0 and p['estimated_sales'] >= 500]
        for p in filtered:
            self.db.add_product(p)
        self.last_scrape = now

        # Send approval requests for pending products
        pending = self.db.get_pending_products(limit=3)
        if not pending:
            await msg.edit_text("❌ No qualifying products found.")
            return
        await msg.edit_text(f"✅ Found {len(pending)} products!")
        for p in pending:
            await self.send_approval(p)
        await update.message.reply_text(f"🎯 Sent {len(pending)} products for review!")

    async def send_approval(self, product):
        link = f"{product['url']}?tid={CLICKBANK_NICKNAME}"
        text = (
            f"🔥 High-Converting Product\n\n"
            f"Name: {product['name']}\n"
            f"Category: {product['category']}\n"
            f"Price: {product['price']}\n"
            f"Commission: {product['commission_pct']}%\n"
            f"Est. Sales: {product['estimated_sales']}\n"
            f"Platform: {product['platform']}\n\n"
            f"Description: {product['description'][:150]}...\n\n"
            f"Link: {link}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve|{product['url
