import os
import sys
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from modules.uptime_checker import handle_uptime
from modules.memory_checker import handle_memory
from modules.bot_killer import handle_kill
from modules.bot_rebooter import handle_restart
from modules.log_reporter import handle_log

async def start_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN missing", file=sys.stderr)
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("uptime", handle_uptime))
    app.add_handler(CommandHandler("memory", handle_memory))
    app.add_handler(CommandHandler("kill", handle_kill))
    app.add_handler(CommandHandler("restart", handle_restart))
    app.add_handler(CommandHandler("log", handle_log))

    await app.initialize()
    await app.start()
    print("Bot started and polling...")

    try:
        await app.updater.start_polling()
        await asyncio.Event().wait()
    finally:
        await app.updater.stop_polling()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(start_bot())
