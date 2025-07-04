import os
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_log(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram send error: {e}")
