from utils.env_reloader import reload_env

async def reload_env_command(update, context):
    reload_env()
    await update.message.reply_text("Environment variables reloaded.")
