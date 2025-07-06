import os
import sys
from telegram.ext import ApplicationBuilder, CommandHandler
from modules.uptime_checker import handle_uptime
from modules.memory_checker import handle_memory
from modules.bot_killer import handle_kill
from modules.bot_rebooter import handle_restart
from modules.log_reporter import handle_log

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in environment.", file=sys.stderr)
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("uptime", handle_uptime))
    app.add_handler(CommandHandler("memory", handle_memory))
    app.add_handler(CommandHandler("kill", handle_kill))
    app.add_handler(CommandHandler("restart", handle_restart))
    app.add_handler(CommandHandler("log", handle_log))

    try:
        await app.run_polling()
    except Exception as e:
        print(f"Error running bot: {e}", file=sys.stderr)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
