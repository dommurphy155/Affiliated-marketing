import os
import asyncio
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
        print("Error: TELEGRAM_BOT_TOKEN not set in environment.", file=sys.stderr)
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()

    # Register your handlers
    app.add_handler(CommandHandler("uptime", handle_uptime))
    app.add_handler(CommandHandler("memory", handle_memory))
    app.add_handler(CommandHandler("kill", handle_kill))
    app.add_handler(CommandHandler("restart", handle_restart))
    app.add_handler(CommandHandler("log", handle_log))

    try:
        await app.run_polling()
    except Exception as e:
        print(f"Error running bot: {e}", file=sys.stderr)
    finally:
        await app.shutdown()
        await app.stop()

def run_bot():
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.sleep(0.1))
        loop.close()

if __name__ == "__main__":
    run_bot()
