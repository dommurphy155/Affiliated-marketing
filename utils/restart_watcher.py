import time
import os
import logging

def watch_and_restart(interval=300):
    """Watches the bot process, restarts if not healthy."""
    while True:
        # Placeholder health check logic here
        healthy = True  # Add real checks
        if not healthy:
            logging.warning("Bot unhealthy, restarting...")
            os.system("pm2 restart bot")
        time.sleep(interval)
