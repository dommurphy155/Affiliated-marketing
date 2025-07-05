from telegram import Update
from telegram.ext import ContextTypes
from modules.utils.product_cache import get_all_cached_products

async def handle_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = get_all_cached_products()
    if not products:
        await update.message.reply_text("❌ No products saved.")
    else:
        reply = "📦 Current Saved Products:\n"
        for idx, p in enumerate(products, 1):
            reply += f"{idx}. {p.get('title', 'No title')} - {p.get('url', 'No link')}\n"
        await update.message.reply_text(reply)
