#!/usr/bin/env python3
"""
Streamlined AI Affiliate Marketing Bot - Lightweight Version
"""

import asyncio
import logging
import os
import json
import sqlite3
import hashlib
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import requests
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp

# Configuration
@dataclass
class Config:
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
    clickbank_nickname: str = os.getenv('CLICKBANK_NICKNAME', '')
    
    # Paths
    data_dir: Path = Path('./data')
    videos_dir: Path = Path('./videos')
    db_path: Path = Path('./data/bot.db')
    
    def __post_init__(self):
        for path in [self.data_dir, self.videos_dir]:
            path.mkdir(exist_ok=True)

config = Config()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Product model
@dataclass
class Product:
    id: str
    name: str
    url: str
    commission: float
    price: float
    rating: float
    description: str
    category: str
    video_path: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

# Database
class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                commission REAL NOT NULL,
                price REAL NOT NULL,
                rating REAL NOT NULL,
                description TEXT,
                category TEXT,
                video_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                products_count INTEGER DEFAULT 0,
                videos_generated INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_product(self, product: Product) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (id, name, url, commission, price, rating, description, category, video_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.id, product.name, product.url, product.commission,
                product.price, product.rating, product.description, 
                product.category, product.video_path
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving product: {e}")
            return False
    
    def get_products(self, limit: int = 10) -> List[Product]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        products = []
        for row in rows:
            products.append(Product(
                id=row[0], name=row[1], url=row[2], commission=row[3],
                price=row[4], rating=row[5], description=row[6], 
                category=row[7], video_path=row[8]
            ))
        
        conn.close()
        return products

# Simple Product Generator (simulated scraping)
class ProductGenerator:
    def __init__(self, nickname: str):
        self.nickname = nickname
        self.product_templates = [
            "AI Writing Assistant Pro", "Crypto Trading Bot", "Fitness Transformation Guide",
            "Social Media Growth Tool", "Email Marketing Mastery", "YouTube Success Formula",
            "Amazon FBA Blueprint", "Dropshipping Secrets", "Instagram Influence Course",
            "TikTok Viral Strategy", "Affiliate Marketing System", "Online Business Builder"
        ]
        self.categories = ["Marketing", "Business", "Health", "Technology", "Education"]
    
    def generate_products(self, count: int = 10) -> List[Product]:
        products = []
        
        for i in range(count):
            name = random.choice(self.product_templates)
            product_id = hashlib.md5(f"{name}{i}".encode()).hexdigest()[:8]
            
            product = Product(
                id=product_id,
                name=f"{name} {random.randint(1, 5)}.0",
                url=f"https://hop.clickbank.net/?affiliate={self.nickname}&vendor={product_id}",
                commission=random.uniform(40, 75),
                price=random.uniform(27, 297),
                rating=random.uniform(4.0, 5.0),
                description=f"High-converting {name.lower()} with proven results",
                category=random.choice(self.categories)
            )
            products.append(product)
        
        return products

# Video Generator
class VideoGenerator:
    def __init__(self):
        self.videos_dir = config.videos_dir
        
    def generate_video(self, product: Product) -> Optional[str]:
        """Generate simple promotional video"""
        try:
            video_path = self.videos_dir / f"{product.id}.mp4"
            
            # Create background with gradient
            bg = self._create_gradient_background()
            
            # Add text overlays
            video = self._add_promotional_text(bg, product)
            
            # Export
            video.write_videofile(
                str(video_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            return str(video_path)
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None
    
    def _create_gradient_background(self) -> mp.VideoClip:
        """Create colorful gradient background"""
        # Create a simple colored background
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        color = random.choice(colors)
        
        return mp.ColorClip(size=(1080, 1920), color=color, duration=6)
    
    def _add_promotional_text(self, video: mp.VideoClip, product: Product) -> mp.VideoClip:
        """Add promotional text overlays"""
        texts = [
            ("🔥 VIRAL PRODUCT", 0, 1.5),
            (f"💰 {product.commission:.0f}% COMMISSION", 1.5, 3),
            (f"⭐ {product.rating:.1f}/5 RATING", 3, 4.5),
            ("🚀 LINK IN BIO", 4.5, 6)
        ]
        
        clips = [video]
        
        for text, start, end in texts:
            txt_clip = mp.TextClip(
                text,
                fontsize=80,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3
            ).set_position('center').set_duration(end - start).set_start(start)
            clips.append(txt_clip)
        
        return mp.CompositeVideoClip(clips)

# Telegram Bot
class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
        self.db = Database(config.db_path)
        self.product_generator = ProductGenerator(config.clickbank_nickname)
        self.video_generator = VideoGenerator()
        
    async def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("products", self.products_command))
        self.application.add_handler(CommandHandler("generate", self.generate_command))
        self.application.add_handler(CommandHandler("videos", self.videos_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("🛍️ Products", callback_data="products")],
            [InlineKeyboardButton("🎬 Generate Videos", callback_data="videos")],
            [InlineKeyboardButton("🔄 New Products", callback_data="generate")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *AI Affiliate Bot - Lite*\n\n"
            "Features:\n"
            "• 🔍 Generate high-ROI products\n"
            "• 🎬 Create viral videos\n"
            "• 📊 Track performance\n"
            "• 💰 Monitor earnings\n\n"
            "Choose an option:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        products = self.db.get_products()
        videos_count = len([p for p in products if p.video_path])
        
        stats_text = f"📊 *Bot Statistics*\n\n"
        stats_text += f"• Products: {len(products)}\n"
        stats_text += f"• Videos Generated: {videos_count}\n"
        stats_text += f"• Est. Earnings: ${sum(p.commission for p in products):.2f}\n"
        stats_text += f"• Avg Commission: {sum(p.commission for p in products)/len(products):.1f}%\n"
        stats_text += f"• Last Update: {datetime.now().strftime('%H:%M')}"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        products = self.db.get_products(limit=5)
        
        if not products:
            await update.message.reply_text("No products found. Use /generate to create some!")
            return
        
        for product in products:
            await self.send_product_info(product, update.message.chat_id)
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 Generating new products...")
        
        products = self.product_generator.generate_products(5)
        saved_count = 0
        
        for product in products:
            if self.db.save_product(product):
                saved_count += 1
        
        await update.message.reply_text(f"✅ Generated {saved_count} new products!")
    
    async def videos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎬 Creating videos...")
        
        products = self.db.get_products(limit=3)
        generated_count = 0
        
        for product in products:
            if not product.video_path:
                video_path = self.video_generator.generate_video(product)
                if video_path:
                    product.video_path = video_path
                    self.db.save_product(product)
                    generated_count += 1
        
        await update.message.reply_text(f"✅ Generated {generated_count} videos!")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🤖 *Available Commands:*

/start - Main menu
/stats - View statistics
/products - Show products
/generate - Generate new products
/videos - Create videos
/help - Show this help

Just type your questions and I'll help! 🚀
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message.text.lower()
        
        if any(word in message for word in ['help', 'commands']):
            await self.help_command(update, context)
        elif any(word in message for word in ['stats', 'statistics']):
            await self.stats_command(update, context)
        elif any(word in message for word in ['products', 'list']):
            await self.products_command(update, context)
        elif any(word in message for word in ['generate', 'new', 'create']):
            await self.generate_command(update, context)
        elif any(word in message for word in ['video', 'videos']):
            await self.videos_command(update, context)
        else:
            await update.message.reply_text(
                "I'm here to help! Use /help to see available commands. 👂"
            )
    
    async def send_product_info(self, product: Product, chat_id: str):
        """Send product information"""
        try:
            message = f"🛍️ *Product Alert*\n\n"
            message += f"📦 *Name:* {product.name}\n"
            message += f"💰 *Commission:* {product.commission:.1f}%\n"
            message += f"💵 *Price:* ${product.price:.2f}\n"
            message += f"⭐ *Rating:* {product.rating:.1f}/5\n"
            message += f"📂 *Category:* {product.category}\n"
            message += f"🔗 *Link:* {product.url}\n\n"
            message += f"💡 *Est. Earnings:* ${product.commission * 5:.2f}/sale"
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Send video if available
            if product.video_path and os.path.exists(product.video_path):
                with open(product.video_path, 'rb') as video:
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=f"🎬 Promotional video for {product.name}"
                    )
        except Exception as e:
            logger.error(f"Error sending product info: {e}")

# Main Bot
class AffiliateBot:
    def __init__(self):
        self.telegram_bot = TelegramBot(config.telegram_bot_token, config.telegram_chat_id)
        self.running = True
        
    async def start(self):
        """Start the bot"""
        logger.info("🤖 Starting Affiliate Bot...")
        
        await self.telegram_bot.setup_handlers()
        await self.telegram_bot.application.initialize()
        await self.telegram_bot.application.start()
        
        # Send startup message
        await self.telegram_bot.bot.send_message(
            chat_id=config.telegram_chat_id,
            text="🚀 *Affiliate Bot is now online!*\n\nUse /start to begin.",
            parse_mode='Markdown'
        )
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
    
    def stop(self):
        self.running = False

# Main execution
async def main():
    try:
        bot = AffiliateBot()
        await bot.start()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
