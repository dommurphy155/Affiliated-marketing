import schedule, time, logging
from modules.video_poster import post_video_logic

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def post_wrap():
    try:
        logging.info("Posting scheduled TikTok...")
        result = post_video_logic()
        logging.info("Posted ✅" if result else "Post failed ❌")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

schedule.every().day.at("10:00").do(post_wrap)
schedule.every().day.at("15:00").do(post_wrap)
schedule.every().day.at("20:00").do(post_wrap)

logging.info("TikTok scheduler running. Awaiting triggers...")

while True:
    schedule.run_pending()
    time.sleep(60)
