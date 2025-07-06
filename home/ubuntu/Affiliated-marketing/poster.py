import asyncio
import logging
import os
import random
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
VIDEO_DIR = os.getenv("VIDEO_DIR", "videos")
CAPTIONS_FILE = os.getenv("CAPTIONS_FILE", "captions.txt")

def random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/91.0 Mobile Safari/537.36"
    ])

async def get_random_video_path() -> Optional[str]:
    videos = list(Path(VIDEO_DIR).glob("*.mp4"))
    if not videos:
        logger.warning("No video files found.")
        return None
    return str(random.choice(videos))

async def get_caption() -> str:
    try:
        with open(CAPTIONS_FILE, "r") as f:
            captions = [line.strip() for line in f if line.strip()]
            return random.choice(captions) if captions else "Check this out!"
    except Exception:
        return "Check this out!"

async def post_video(video_path: Optional[str] = None, caption: Optional[str] = None) -> str:
    video_path = video_path or await get_random_video_path()
    caption = caption or await get_caption()

    if not video_path:
        return "No video found to upload."

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--start-maximized"])
            context = await browser.new_context(
                user_agent=random_user_agent(),
                viewport={"width": 1280, "height": 720},
                java_script_enabled=True,
            )
            await context.add_init_script(path="stealth.min.js")

            page = await context.new_page()
            logger.info("Logging into TikTok...")
            await page.goto("https://www.tiktok.com/login/phone-or-email/email", timeout=60000)

            await page.fill('input[name="email"]', TIKTOK_EMAIL)
            await page.fill('input[name="password"]', TIKTOK_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(7000)

            if "login" in page.url:
                raise Exception("Login failed.")

            logger.info("Uploading video to TikTok...")
            await page.goto("https://www.tiktok.com/upload", timeout=60000)
            await page.set_input_files('input[type="file"]', video_path)

            await page.wait_for_selector('textarea[placeholder="Describe your video"]', timeout=30000)
            await page.fill('textarea[placeholder="Describe your video"]', caption)
            await page.click('button:has-text("Post")')
            await page.wait_for_timeout(8000)

            await browser.close()
            return f"Video posted successfully: {Path(video_path).name}"

    except PlaywrightTimeoutError:
        logger.exception("Timeout error during posting.")
        return "Timeout while trying to post video."

    except Exception as e:
        logger.exception("Error posting video.")
        return f"Failed to post video: {str(e)}"

if __name__ == "__main__":
    result = asyncio.run(post_video())
    print(result)
