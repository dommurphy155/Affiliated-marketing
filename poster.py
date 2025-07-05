import asyncio
from playwright.async_api import async_playwright
import logging
import os

logging.basicConfig(level=logging.INFO)

TIKTOK_LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"

async def post_to_tiktok(video_path, email, password):
    logging.info("Launching browser for TikTok post automation")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless=False to debug visually
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(TIKTOK_LOGIN_URL)
        await page.wait_for_timeout(3000)

        # Login steps — email login flow
        await page.fill('input[name="email"]', email)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')

        # Check login success (example: presence of upload button)
        try:
            await page.wait_for_selector('button[aria-label="Upload video"]', timeout=15000)
        except Exception:
            logging.error("Login failed or upload button not found")
            await browser.close()
            raise Exception("TikTok login failed")

        # Navigate to upload page (might vary)
        await page.goto("https://www.tiktok.com/upload")
        await page.wait_for_selector('input[type="file"]')

        # Upload video
        input_file = await page.query_selector('input[type="file"]')
        await input_file.set_input_files(video_path)

        # Wait upload progress (naive wait)
        await page.wait_for_timeout(10000)

        # Submit upload (assuming a button available)
        await page.click('button[data-e2e="upload-post-button"]')
        await page.wait_for_timeout(5000)

        await browser.close()
        logging.info("Video uploaded successfully to TikTok")
        return "Video uploaded to TikTok"
