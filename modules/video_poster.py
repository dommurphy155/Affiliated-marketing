from telegram import Update
from telegram.ext import ContextTypes
from modules.video_generator import generate_video_for_latest_product
from modules.tiktok_uploader import upload_to_tiktok
import logging
from modules.video_generator import generate_video_for_latest_product
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🎬 Generating video...")
        filepath = generate_video_for_latest_product()
        success = upload_to_tiktok(filepath)
        if success:
            await update.message.reply_text("✅ Posted to TikTok successfully!")
        else:
            await update.message.reply_text("❌ Failed to post video.")
    except Exception as e:
        logging.error(f"Post video error: {e}")
        await update.message.reply_text("⚠️ Error posting video.")

def post_video_logic():
    filepath = generate_video_for_latest_product()
    return upload_to_tiktok(filepath)
