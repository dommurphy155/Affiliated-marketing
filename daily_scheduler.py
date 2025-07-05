import schedule
import time
import logging
from modules.video_poster import post_video_logic

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def daily_tiktok_post():
    try:
        logging.info("Running TikTok post...")
        post_video_logic()
        logging.info("Video posted successfully.")
    except Exception as e:
        logging.error(f"Failed to post video: {e}")

# Schedule job 3 times a day
schedule.every().day.at("10:00").do(daily_tiktok_post)
schedule.every().day.at("14:00").do(daily_tiktok_post)
schedule.every().day.at("18:00").do(daily_tiktok_post)

logging.info("Scheduler started. Waiting for next run...")

while True:
    schedule.run_pending()
    time.sleep(60)
