import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="💸 Money printer is ON!")

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Placeholder for actual data - update this with real earnings or logs
    message = f"📈 Daily Report ({now}):\n- Earnings: £0\n- Clicks: 0\n- Conversions: 0"
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))

    # Daily report job
    application.job_queue.run_daily(daily_report, time=datetime.now().time())

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
