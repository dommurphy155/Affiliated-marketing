import os
import time
from content_generator import generate_content
from scheduler import schedule_posts
from telemetry import send_telegram_log

def autopost_loop():
    while True:
        try:
            content = generate_content()
            schedule_posts(content)
            send_telegram_log("✅ Content posted successfully.")
        except Exception as e:
            send_telegram_log(f"❌ Post failed: {str(e)}")
        time.sleep(3600)  # Wait 1 hour between posts

if __name__ == "__main__":
    autopost_loop()
