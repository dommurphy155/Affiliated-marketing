# login_tiktok.py
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import time

load_dotenv()

EMAIL = os.getenv("TIKTOK_EMAIL")
PASSWORD = os.getenv("TIKTOK_PASSWORD")

async def login_to_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://www.tiktok.com/login/phone-or-email/email", timeout=60000)

            # Accept cookies
            try:
                await page.locator('button:has-text("Accept all")').click(timeout=3000)
            except:
                pass

            await page.fill('input[name="email"]', EMAIL)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(8000)

            content = await page.content()
            if "For You" in content or "Upload" in content:
                print("✅ TikTok login successful.")
            else:
                print("❌ TikTok login may have failed.")

        except Exception as e:
            print(f"🚨 Error during login: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_to_tiktok())

