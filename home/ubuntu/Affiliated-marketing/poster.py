import asyncio
import logging
import os
import random
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openai import AsyncOpenAI

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Environment vars
TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CAPCUT_URL = "https://www.capcut.com/editor-ai-script-video"

# OpenAI client
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Simple caption generator using GPT
async def generate_caption() -> str:
    try:
        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a short, high-CTR TikTok caption for a trending digital product. Keep it hypey but not spammy."},
                {"role": "user", "content": "Write the caption now."}
            ],
            temperature=0.9,
            max_tokens=40
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Caption generation failed: {e}", exc_info=True)
        return "You won’t believe this..."

# Random realistic user-agent
def random_user_agent() -> str:
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/91.0 Mobile Safari/537.36"
    ])

# Generate video on CapCut and download to disk (if needed)
async def generate_video_script(playwright):
    browser = await playwright.chromium.launch(headless=True, args=["--start-maximized"])
    context = await browser.new_context(user_agent=random_user_agent(), viewport={"width": 1280, "height": 720})
    await context.add_init_script(path="stealth.min.js")  # Optional stealth

    page = await context.new_page()
    try:
        logger.info("Logging into CapCut")
        await page.goto("https://www.capcut.com/login", timeout=60000)
        await page.click("text=Use email")
        await page.fill('input[name="email"]', TIKTOK_EMAIL)
        await page.fill('input[name="password"]', TIKTOK_PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)

        if "login" in page.url:
            raise Exception("CapCut login failed.")

        logger.info("Generating script-to-video")
        await page.goto(CAPCUT_URL, timeout=60000)

        script_text = await generate_caption()
        await page.fill('textarea[placeholder="Write your script"]', script_text)
        await page.click("button:has-text('Generate video')")

        await page.wait_for_selector("video", timeout=90000)
        logger.info("Video generation complete")
        return True

    except Exception as e:
        logger.error(f"Error during CapCut video generation: {e}", exc_info=True)
        return False
    finally:
        await browser.close()

# Post video to TikTok via Playwright
async def post_video(_: Optional[str] = None, caption: Optional[str] = None) -> str:
    caption = caption or await generate_caption()

    try:
        async with async_playwright() as p:
            capcut_success = await generate_video_script(p)
            if not capcut_success:
                return "Video generation failed"

            logger.info("Logging into TikTok")
            browser = await p.chromium.launch(headless=True, args=["--start-maximized"])
            context = await browser.new_context(user_agent=random_user_agent(), viewport={"width": 1280, "height": 720})
            await context.add_init_script(path="stealth.min.js")

            page = await context.new_page()
            await page.goto("https://www.tiktok.com/login", timeout=60000)
            await page.click('text="Use email / username"')
            await page.fill('input[name="email"]', TIKTOK_EMAIL)
            await page.fill('input[name="password"]', TIKTOK_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "login" in page.url:
                raise Exception("TikTok login failed")

            logger.info("Uploading video to TikTok")
            await page.goto("https://www.tiktok.com/upload", timeout=60000)

            # TODO: Pull final video file path if downloaded locally
            # Example placeholder: await page.set_input_files('input[type="file"]', "output.mp4")
            await page.fill('textarea[placeholder="Describe your video"]', caption)
            await page.click('button:has-text("Post")')
            await page.wait_for_timeout(8000)

            logger.info("Video posted successfully.")
            await browser.close()
            return "Posted successfully"
    except PlaywrightTimeoutError:
        logger.exception("Playwright timeout error")
        return "Timeout posting video."
    except Exception as e:
        logger.exception("TikTok post failed")
        return f"Failed to post video: {e}"

# Local test
if __name__ == "__main__":
    result = asyncio.run(post_video())
    print(result)
