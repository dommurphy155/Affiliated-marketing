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

load_dotenv()

required_vars = [
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "OPENAI_API_KEY",
    "CLICKBANK_NICKNAME", "TIKTOK_EMAIL", "TIKTOK_PASSWORD",
    "CAPCUT_EMAIL", "CAPCUT_PASSWORD"
]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

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

# The rest of the script continues...
# [Truncated due to size constraints – will split if needed]
