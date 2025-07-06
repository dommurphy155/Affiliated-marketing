import asyncio
import logging
import os
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import openai

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TIKTOK_EMAIL = os.getenv("TIKTOK_EMAIL")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
CAPCUT_EMAIL = TIKTOK_EMAIL  # Same creds
CAPCUT_PASSWORD = TIKTOK_PASSWORD
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Generate video script with OpenAI (GPT-4/3.5)
async def generate_script(product_name, product_url):
    prompt = (
        f"Write a short, viral TikTok video script promoting this product: {product_name}.\n"
        f"Include a call to action and use trendy, engaging language. Product URL: {product_url}"
    )
    try:
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.9,
            )
        )
        script = response.choices[0].message.content.strip()
        logger.info(f"Generated script: {script}")
        return script
    except Exception as e:
        logger.error(f"OpenAI script generation failed: {e}")
        return "Check out this amazing product! Link in bio."

# Stealth browser setup with Playwright
async def launch_stealth_browser(playwright):
    chromium = playwright.chromium
    browser = await chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = await browser.new_context(
        user_agent=random_user_agent(),
        viewport={"width": 1280, "height": 720},
    )
    # Insert stealth JS if available here (e.g. from stealth.min.js)
    # await context.add_init_script(path="stealth.min.js")  # Optional
    return browser, context

def random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/91.0 Mobile Safari/537.36",
    ]
    return random.choice(agents)

async def login_tiktok(page):
    logger.info("Logging into TikTok...")
    await page.goto("https://www.tiktok.com/login", timeout=60000)
    await page.click('text="Use email / username"')
    await page.fill('input[name="email"]', TIKTOK_EMAIL)
    await page.fill('input[name="password"]', TIKTOK_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_timeout(6000)
    if "login" in page.url:
        raise RuntimeError("TikTok login failed or blocked.")
    logger.info("TikTok login successful.")

async def login_capcut(page):
    logger.info("Logging into CapCut...")
    await page.goto("https://www.capcut.com/login", timeout=60000)
    await page.fill('input[type="email"]', CAPCUT_EMAIL)
    await page.fill('input[type="password"]', CAPCUT_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_timeout(6000)
    if "login" in page.url:
        raise RuntimeError("CapCut login failed or blocked.")
    logger.info("CapCut login successful.")

async def create_video_on_capcut(page, script_text):
    logger.info("Creating video on CapCut with script...")
    await page.goto("https://www.capcut.com/script-to-video", timeout=60000)
    await page.fill('textarea#scriptInput', script_text)
    await page.click('button:has-text("Generate Video")')
    # Wait for video to finish rendering — timeout after 5 minutes max
    for _ in range(60):
        try:
            await page.wait_for_selector('video[playsinline]', timeout=5000)
            logger.info("Video generated successfully.")
            return True
        except PlaywrightTimeoutError:
            logger.info("Waiting for video generation to complete...")
    logger.error("Video generation timed out.")
    return False

async def post_video():
    # Select a product - In practice, pull from DB or scrape results
    product_name = "Sample Product"
    product_url = "https://example.com/product"

    script_text = await generate_script(product_name, product_url)

    async with async_playwright() as p:
        browser, context = await launch_stealth_browser(p)
        page = await context.new_page()

        # Login CapCut and generate video
        await login_capcut(page)
        video_ready = await create_video_on_capcut(page, script_text)
        if not video_ready:
            await browser.close()
            return "Failed to generate video."

        # Grab video URL or download link if possible (CapCut currently has no API for this)
        # For simplicity, assume video saved locally as 'latest.mp4' in your environment,
        # or stream the video URL.

        # Login TikTok and post video
        await login_tiktok(page)
        await page.goto("https://www.tiktok.com/upload", timeout=60000)

        # You would need to set file input here if you had local file; CapCut direct upload can be tricky.
        # Placeholder: await page.set_input_files('input[type="file"]', 'latest.mp4')

        # Fill caption with generated script
        await page.fill('textarea[placeholder="Describe your video"]', script_text)
        await page.click('button:has-text("Post")')
        await page.wait_for_timeout(8000)

        await browser.close()
        return f"Video posted for product: {product_name}"

if __name__ == "__main__":
    result = asyncio.run(post_video())
    print(result)
