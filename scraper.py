import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLICKBANK_TOP_OFFERS_URL = "https://www.clickbank.com/top-marketplaces/"
AMAZON_UK_TRENDING_URL = "https://www.amazon.co.uk/gp/bestsellers/digital-text/362250031"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

async def fetch_html(session, url):
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"[FETCH ERROR] {url} - {e}")
        return ""

def calculate_viral_score(gravity, commission):
    try:
        gravity_val = float(gravity)
        commission_val = float(commission.strip('%').replace('$', ''))
        return gravity_val * commission_val
    except Exception:
        return 0

def parse_clickbank_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = []
    rows = soup.select("table.marketplace-table tr")[1:]

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        try:
            name = cols[0].get_text(strip=True)
            price = cols[1].get_text(strip=True)
            commission = cols[2].get_text(strip=True)
            gravity = cols[3].get_text(strip=True)
            url = cols[0].find("a")["href"] if cols[0].find("a") else ""
            viral_score = calculate_viral_score(gravity, commission)
            offers.append({
                "source": "ClickBank",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": gravity,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"[CLICKBANK PARSE ERROR] {e}")
    return offers

def parse_amazon_uk_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = []
    items = soup.select("div.zg-grid-general-faceout")

    for item in items:
        try:
            title = item.select_one("div.p13n-sc-truncated, div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y").get_text(strip=True)
            url_tag = item.find("a", href=True)
            url = "https://www.amazon.co.uk" + url_tag["href"] if url_tag else ""
            offers.append({
                "source": "Amazon UK",
                "name": title,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "N/A",
                "url": url,
                "viral_score": 0
            })
        except Exception as e:
            logger.warning(f"[AMAZON PARSE ERROR] {e}")
    return offers

async def scrape_clickbank():
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, CLICKBANK_TOP_OFFERS_URL)
        return parse_clickbank_offers(html) if html else []

async def scrape_amazon_uk():
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, AMAZON_UK_TRENDING_URL)
        return parse_amazon_uk_offers(html) if html else []

async def scrape_all():
    logger.info("Scraping all sources...")
    results = await asyncio.gather(
        scrape_clickbank(),
        scrape_amazon_uk(),
    )
    all_products = [item for sublist in results for item in sublist]
    # Sort by viral score if present
    all_products.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
    logger.info(f"Scraped total products: {len(all_products)}")
    return all_products

if __name__ == "__main__":
    offers = asyncio.run(scrape_all())
    for offer in offers[:10]:
        print(f"{offer['source']} | {offer['name']} | {offer['url']}")
