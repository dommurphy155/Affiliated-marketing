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
VIDEO_DIR = os.getenv("VIDEO_DIR", "videos")  # You can keep if needed or leave empty

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0 Mobile Safari/537.36",
]

def random_user_agent() -> str:
    return random.choice(USER_AGENTS)

async def post_video(video_path: Optional[str] = None, caption: Optional[str] = None) -> str:
    caption = caption or "Check this out!"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--start-maximized"])
            context = await browser.new_context(
                user_agent=random_user_agent(),
                viewport={"width": 1280, "height": 720},
                java_script_enabled=True,
            )
            # Add stealth here: example with eval scripts or plugins if you have stealth.min.js
            # await context.add_init_script(path="stealth.min.js")

            page = await context.new_page()
            logger.info("Navigating to TikTok login page")
            await page.goto("https://www.tiktok.com/login", timeout=60000)

            # Login via email
            await page.click('text="Use email / username"', timeout=10000)
            await page.fill('input[name="email"]', TIKTOK_EMAIL)
            await page.fill('input[name="password"]', TIKTOK_PASSWORD)
            await page.click('button[type="submit"]')

            await page.wait_for_timeout(5000)
            if "login" in page.url:
                raise Exception("Login failed or blocked")

            logger.info("Login successful. Navigating to upload page.")
            await page.goto("https://www.tiktok.com/upload", timeout=60000)

            if not video_path:
                return "No video path provided."

            await page.set_input_files('input[type="file"]', video_path)
            await page.fill('textarea[placeholder="Describe your video"]', caption)
            await page.click('button:has-text("Post")')
            await page.wait_for_timeout(8000)

            logger.info("Video posted successfully.")
            await browser.close()
            return f"Video posted: {Path(video_path).name}"

    except PlaywrightTimeoutError:
        logger.exception("Playwright timeout error")
        return "Timeout while posting video."
    except Exception as e:
        logger.exception("Unexpected error during TikTok posting")
        return f"Failed to post video: {str(e)}"

if __name__ == "__main__":
    result = asyncio.run(post_video())
    print(result)
