import subprocess
from telegram import Update
from telegram.ext import ContextTypes

async def handle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run([
            'pm2', 'logs', 'bot', '--lines', '50', '--raw'
        ], capture_output=True, text=True, timeout=10)
        logs = result.stdout.strip()
        if not logs:
            logs = 'No logs found.'
    except Exception as e:
        logs = f'Failed to fetch logs: {e}'

    max_length = 4000
    for i in range(0, len(logs), max_length):
        chunk = logs[i:i+max_length]
        await update.message.reply_text(f'', parse_mode='Markdown')
