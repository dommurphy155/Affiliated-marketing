import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
import json
import hashlib
import random
from urllib.parse import urlparse

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.error import NetworkError, TimedOut, BadRequest

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import openai
import aiohttp

# Load environment variables
load_dotenv()

def validate_env_vars():
    """Validate required environment variables"""
    required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "OPENAI_API_KEY", "CLICKBANK_NICKNAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    return True

# Validate environment
validate_env_vars()

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLICKBANK_NICKNAME = os.getenv("CLICKBANK_NICKNAME")

# Configuration
MAX_PRODUCTS_PER_SCRAPE = int(os.getenv("MAX_PRODUCTS_PER_SCRAPE", "5"))
MIN_COMMISSION_PCT = float(os.getenv("MIN_COMMISSION_PCT", "15.0"))
MIN_ESTIMATED_SALES = int(os.getenv("MIN_ESTIMATED_SALES", "500"))
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("affiliate_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "affiliate_bot.db"

def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                price TEXT,
                commission_pct REAL,
                estimated_sales INTEGER,
                description TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_url TEXT,
                amount REAL,
                commission_pct REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                platform TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

init_database()

class DatabaseManager:
    """Handles database operations"""
    
    @staticmethod
    def add_product(product_data):
        """Add product to database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO products 
                (url, name, category, price, commission_pct, estimated_sales, description, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data['url'], product_data['name'], product_data['category'],
                product_data['price'], product_data.get('commission_pct', 0),
                product_data.get('estimated_sales', 0), product_data['description'],
                product_data.get('platform', 'unknown')
            ))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_unseen_products(limit=10):
        """Get pending products"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM products 
                WHERE status = 'pending' 
                ORDER BY commission_pct DESC, estimated_sales DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            products = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return products
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def update_product_status(product_url, status):
        """Update product status"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE products SET status = ? WHERE url = ?', (status, product_url))
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating product status: {e}")
        finally:
            conn.close()
    
    @staticmethod
    def get_earnings_summary(days=30):
        """Get earnings summary"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sales,
                    COALESCE(SUM(amount), 0) as total_earnings,
                    COALESCE(AVG(commission_pct), 0) as avg_commission
                FROM earnings 
                WHERE date >= datetime('now', '-{} days')
            '''.format(days))
            
            result = cursor.fetchone()
            return {
                'total_sales': result[0] or 0,
                'total_earnings': result[1] or 0.0,
                'avg_commission': result[2] or 0.0
            }
        except Exception as e:
            logger.error(f"Error getting earnings: {e}")
            return {'total_sales': 0, 'total_earnings': 0.0, 'avg_commission': 0.0}
        finally:
            conn.close()

class PlatformScraper:
    """Handles platform scraping"""
    
    @staticmethod
    async def scrape_clickbank():
        """Scrape ClickBank marketplace"""
        logger.info("Scraping ClickBank marketplace...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                await page.goto("https://marketplace.clickbank.com/", timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Navigate to marketplace
                try:
                    await page.click("text=Marketplace", timeout=5000)
                    await page.wait_for_timeout(2000)
                except:
                    pass
                
                # Get products
                products = []
                try:
                    product_cards = await page.query_selector_all('[data-testid="product-card"]')
                    if not product_cards:
                        product_cards = await page.query_selector_all('.product-card, .marketplace-item')
                    
                    for i, card in enumerate(product_cards[:5]):
                        try:
                            title_elem = await card.query_selector('h3, .product-title, .title')
                            gravity_elem = await card.query_selector('[data-testid="gravity"], .gravity')
                            commission_elem = await card.query_selector('[data-testid="commission"], .commission')
                            
                            if title_elem:
                                title = await title_elem.inner_text()
                                gravity_text = await gravity_elem.inner_text() if gravity_elem else "0"
                                commission_text = await commission_elem.inner_text() if commission_elem else "0"
                                
                                gravity_num = float(''.join(filter(str.isdigit, gravity_text))) if gravity_text else 0
                                commission_num = float(''.join(filter(str.isdigit, commission_text))) if commission_text else 0
                                
                                if gravity_num > 30 and commission_num > MIN_COMMISSION_PCT:
                                    product = {
                                        "name": title.strip(),
                                        "price": "Variable",
                                        "category": "Digital Products",
                                        "description": f"High-converting product with gravity {gravity_num}",
                                        "url": f"https://marketplace.clickbank.com/product/{hashlib.md5(title.encode()).hexdigest()[:8]}",
                                        "commission_pct": commission_num,
                                        "estimated_sales": int(gravity_num * 15),
                                        "platform": "ClickBank"
                                    }
                                    products.append(product)
                        except Exception as e:
                            logger.error(f"Error extracting product {i}: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"Error finding products: {e}")
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"ClickBank scraping failed: {e}")
            return []
    
    @staticmethod
    async def scrape_amazon_associates():
        """Scrape Amazon best sellers"""
        logger.info("Scraping Amazon Associates...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                await page.goto("https://www.amazon.co.uk/gp/bestsellers", timeout=30000)
                await page.wait_for_timeout(2000)
                
                products = []
                try:
                    product_items = await page.query_selector_all('[data-testid="product-item"], .zg-item-immersion')
                    
                    for i, item in enumerate(product_items[:3]):
                        try:
                            title_elem = await item.query_selector('h2 a, .product-title a')
                            price_elem = await item.query_selector('.price, .a-price-whole')
                            
                            if title_elem:
                                title = await title_elem.inner_text()
                                url = await title_elem.get_attribute("href")
                                price = await price_elem.inner_text() if price_elem else "Check Amazon"
                                
                                full_url = f"https://www.amazon.co.uk{url}" if url.startswith('/') else url
                                
                                product = {
                                    "name": title.strip(),
                                    "price": price,
                                    "category": "Consumer Products",
                                    "description": "Best-selling product from Amazon",
                                    "url": full_url,
                                    "commission_pct": 8.0,
                                    "estimated_sales": 1000,
                                    "platform": "Amazon"
                                }
                                products.append(product)
                        except Exception as e:
                            logger.error(f"Error extracting Amazon product {i}: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"Error finding Amazon products: {e}")
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"Amazon scraping failed: {e}")
            return []

class AffiliateBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        self.db = DatabaseManager()
        self.scraper = PlatformScraper()
        self.pending_approvals = {}
        self.last_scrape_time = 0
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("findproducts", self.find_products))
        self.app.add_handler(CommandHandler("earnings", self.earnings))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.inline_button_handler))
        self.app.add_error_handler(self.error_handler)
        
        logger.info("Affiliate Bot initialized successfully")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_message = """
🚀 **Affiliate Marketing Bot Active!**

**Commands:**
• /findproducts - Find high-converting products
• /earnings - View earnings summary
• /status - Bot status
• /help - Show help

**Features:**
• Multi-platform product scraping
• Automated video script generation
• Real-time earnings tracking
• Smart product filtering

Ready to find profitable products! 💰
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """
**Bot Commands:**

**/findproducts** - Scrape platforms for high-converting products
**/earnings** - View earnings summary
**/status** - Check bot status

**How it works:**
1. Bot scrapes affiliate platforms
2. Filters products by commission % and sales
3. Sends recommendations for approval
4. Generates video scripts for approved products
5. Tracks earnings automatically

**Success Tips:**
• Approve products with >20% commission
• Focus on trending categories
• Use generated scripts for videos
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status command"""
        db_status = "✅ Connected" if os.path.exists(DB_PATH) else "❌ Disconnected"
        
        time_since_scrape = time.time() - self.last_scrape_time
        last_scrape = f"{int(time_since_scrape/3600)}h {int((time_since_scrape%3600)/60)}m ago" if self.last_scrape_time > 0 else "Never"
        
        pending_products = len(self.db.get_unseen_products())
        
        status_message = f"""
📊 **Bot Status**

🔌 **System:** Online
💾 **Database:** {db_status}
🕒 **Last Scrape:** {last_scrape}
📦 **Pending Products:** {pending_products}
⚙️ **Scrape Interval:** {SCRAPE_INTERVAL_HOURS}h
🎯 **Min Commission:** {MIN_COMMISSION_PCT}%
📈 **Min Sales:** {MIN_ESTIMATED_SALES}

Ready to find profitable products! 🚀
        """
        await update.message.reply_text(status_message, parse_mode='Markdown')

    async def find_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Find products command"""
        current_time = time.time()
        if current_time - self.last_scrape_time < SCRAPE_INTERVAL_HOURS * 3600:
            remaining_time = SCRAPE_INTERVAL_HOURS * 3600 - (current_time - self.last_scrape_time)
            await update.message.reply_text(
                f"⏳ Please wait {int(remaining_time/3600)}h {int((remaining_time%3600)/60)}m before next scrape."
            )
            return
        
        status_message = await update.message.reply_text("🔍 **Searching for products...**")
        
        try:
            unseen_products = self.db.get_unseen_products(MAX_PRODUCTS_PER_SCRAPE)
            
            if not unseen_products:
                await status_message.edit_text("🔍 **Scraping fresh products...**")
                
                scraping_tasks = [
                    self.scraper.scrape_clickbank(),
                    self.scraper.scrape_amazon_associates(),
                ]
                
                results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                all_products = []
                for result in results:
                    if isinstance(result, list):
                        all_products.extend(result)
                    else:
                        logger.error(f"Scraping error: {result}")
                
                filtered_products = [
                    p for p in all_products 
                    if p.get('commission_pct', 0) >= MIN_COMMISSION_PCT 
                    and p.get('estimated_sales', 0) >= MIN_ESTIMATED_SALES
                ]
                
                for product in filtered_products:
                    self.db.add_product(product)
                
                unseen_products = self.db.get_unseen_products(MAX_PRODUCTS_PER_SCRAPE)
                self.last_scrape_time = current_time
            
            if not unseen_products:
                await status_message.edit_text("❌ **No qualifying products found.**")
                return
            
            await status_message.edit_text(f"✅ **Found {len(unseen_products)} products!**")
            
            for product in unseen_products:
                await self.send_product_for_approval(product)
            
            await update.message.reply_text(
                f"🎯 **Sent {len(unseen_products)} products for review!**"
            )
            
        except Exception as e:
            logger.error(f"Error in find_products: {e}")
            await status_message.edit_text(f"❌ **Error:** {str(e)}")

    async def send_product_for_approval(self, product):
        """Send product for approval"""
        try:
            affiliate_link = f"{product['url']}?tid={CLICKBANK_NICKNAME}"
            
            caption = f"""
🔥 **High-Converting Product**

📦 **Name:** {product['name']}
🏷️ **Category:** {product['category']}
💰 **Price:** {product['price']}
📈 **Commission:** {product['commission_pct']}%
🎯 **Est. Sales:** {product['estimated_sales']}
🌐 **Platform:** {product['platform']}

💡 **Description:** {product['description'][:150]}...

🔗 **Link:** {affiliate_link}
            """
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve|{product['url']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject|{product['url']}"),
                ],
                [
                    InlineKeyboardButton("📝 Generate Script", callback_data=f"script|{product['url']}"),
                ]
            ])
            
            sent_message = await self.app.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=caption,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            self.pending_approvals[sent_message.message_id] = product
                
        except Exception as e:
            logger.error(f"Error sending product for approval: {e}")

    async def inline_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data.split("|")
            if len(data) != 2:
                await query.edit_message_text("⚠️ Invalid callback data.")
                return
            
            action, product_url = data
            message_id = query.message.message_id
            
            if message_id not in self.pending_approvals:
                await query.edit_message_text("⚠️ Product session expired.")
                return
            
            product = self.pending_approvals[message_id]
            
            if action == "approve":
                self.db.update_product_status(product_url, "approved")
                await query.edit_message_text(
                    query.message.text + "\n\n✅ **APPROVED**"
                )
                
            elif action == "reject":
                self.db.update_product_status(product_url, "rejected")
                await query.edit_message_text(
                    query.message.text + "\n\n❌ **REJECTED**"
                )
                
            elif action == "script":
                await query.edit_message_text(
                    query.message.text + "\n\n📝 **Generating script...**"
                )
                script = await self.generate_video_script(product)
                
                script_message = f"""
🎬 **TikTok Script Generated:**

{script}

💡 **Next Steps:**
1. Record video using this script
2. Add product link in bio
3. Use trending hashtags
4. Post during peak hours
                """
                
                await self.app.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=script_message,
                    parse_mode='Markdown'
                )
            
            if message_id in self.pending_approvals:
                del self.pending_approvals[message_id]
                
        except Exception as e:
            logger.error(f"Error handling button: {e}")
            await query.edit_message_text("❌ Error processing request.")

    async def generate_video_script(self, product):
        """Generate video script using OpenAI"""
        try:
            prompt = f"""
Create a viral TikTok script for this product:

Product: {product['name']}
Category: {product['category']}
Price: {product['price']}
Commission: {product['commission_pct']}%
Description: {product['description']}

Requirements:
- Hook viewers in first 3 seconds
- 60-90 seconds total
- Include problem and solution
- Natural product integration
- Strong call-to-action
- Conversational tone

Format as structured script with timing.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return f"Script generation failed: {str(e)}"

    async def earnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Earnings command"""
        try:
            daily = self.db.get_earnings_summary(1)
            weekly = self.db.get_earnings_summary(7)
            monthly = self.db.get_earnings_summary(30)
            
            earnings_message = f"""
💰 **Earnings Summary**

📅 **Today:**
• Sales: {daily['total_sales']}
• Earnings: £{daily['total_earnings']:.2f}
• Avg Commission: {daily['avg_commission']:.1f}%

📊 **This Week:**
• Sales: {weekly['total_sales']}
• Earnings: £{weekly['total_earnings']:.2f}
• Avg Commission: {weekly['avg_commission']:.1f}%

📈 **This Month:**
• Sales: {monthly['total_sales']}
• Earnings: £{monthly['total_earnings']:.2f}
• Avg Commission: {monthly['avg_commission']:.1f}%

Keep promoting high-converting products! 🎯
            """
            
            await update.message.reply_text(earnings_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting earnings: {e}")
            await update.message.reply_text("❌ Error retrieving earnings.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        logger.error(f"Bot error: {context.error}")
        
        try:
            if update and hasattr(update, 'effective_chat'):
                await context.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=f"⚠️ Bot Error: {str(context.error)[:100]}..."
                )
        except Exception as e:
            logger.error(f"Could not send error message: {e}")

    def run(self):
        """Run the bot"""
        logger.info("Starting Affiliate Bot...")
        try:
            self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            raise

if __name__ == "__main__":
    bot = AffiliateBot()
    bot.run()
