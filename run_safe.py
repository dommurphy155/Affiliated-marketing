import asyncio
from main import AffiliateBot

def run_bot():
    try:
        asyncio.run(AffiliateBot().run())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(AffiliateBot().run())

if __name__ == "__main__":
    run_bot()
