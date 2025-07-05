# playwright_tiktok_login.py

import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

load_dotenv()

TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")

async def login_to_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True for stealth
        context = await browser.new_context()
        page = await context.new_page()

        # Go to TikTok login page
        await page.goto("https://www.tiktok.com/login/phone-or-email/email")

        # Accept cookies if prompted
        try:
            await page.locator('button:has-text("Accept all")').click(timeout=3000)
        except:
            pass

        # Fill email and password fields
        await page.fill('input[name="email"]', TIKTOK_EMAIL)
        await page.fill('input[name="password"]', TIKTOK_PASSWORD)

        # Click login button
        await page.click('button[type="submit"]')

        # Wait for navigation or error
        await page.wait_for_timeout(5000)

        # Confirm login by checking if home page is visible
        if "For You" in await page.content():
            print("✅ Logged in to TikTok successfully.")
        else:
            print("❌ Failed to log in.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_to_tiktok())
