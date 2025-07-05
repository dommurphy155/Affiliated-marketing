from modules.utils.product_cache import is_cached, add_to_cache

async def handle(update, context):
    product = await scrape_new_product()
    if is_cached(product['id']):
        await update.message.reply_text("⚠️ Product already posted. Finding another...")
        return
    add_to_cache(product['id'])
    await update.message.reply_text(f"✅ New Product:\n{product['title']}\n{product['url']}")
