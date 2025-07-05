from modules.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

async def some_handler(update, context):
    if not rate_limiter.allow(update.effective_user.id):
        await update.message.reply_text("Too many requests. Try again later.")
        return
    # handler logic
