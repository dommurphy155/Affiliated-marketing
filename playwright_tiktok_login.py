# playwright_tiktok_login.py

import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

load_dotenv()

TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")

async def login_to_tiktok():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Headless for stealth
            context = await browser.new_context()
            page = await context.new_page()

            await stealth_async(page)  # <- Stealth mode enabled

            print("🔍 Navigating to TikTok login page...")
            await page.goto("https://www.tiktok.com/login/phone-or-email/email", timeout=60000)

            try:
                await page.locator('button:has-text("Accept all")').click(timeout=3000)
            except:
                pass  # No cookie popup

            print("📧 Entering login credentials...")
            await page.fill('input[name="email"]', TIKTOK_EMAIL)
            await page.fill('input[name="password"]', TIKTOK_PASSWORD)

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(6000)

            # Check for login success
            content = await page.content()
            if "For You" in content or "Upload" in content:
                print("✅ Successfully logged into TikTok.")
            else:
                print("❌ Login may have failed. Please check credentials or verify captcha manually.")

            await browser.close()

    except Exception as e:
        print(f"❌ Exception during TikTok login: {e}")

if __name__ == "__main__":
    asyncio.run(login_to_tiktok())
