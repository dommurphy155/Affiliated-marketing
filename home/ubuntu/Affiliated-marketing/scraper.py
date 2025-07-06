import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLICKBANK_TOP_OFFERS_URL = "https://www.clickbank.com/top-marketplaces/"  # Replace with actual top offers URL if different

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=30) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""

def parse_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    # Example parsing logic; adjust based on actual page structure
    # This is a generic example — you will likely want to tweak selectors based on ClickBank’s actual page
    offer_rows = soup.select("table.marketplace-table tr")[1:]  # Skip header row
    for row in offer_rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        try:
            name = cols[0].get_text(strip=True)
            price = cols[1].get_text(strip=True)
            commission = cols[2].get_text(strip=True)
            gravity = cols[3].get_text(strip=True)
            url = cols[0].find("a")["href"] if cols[0].find("a") else ""
            viral_score = calculate_viral_score(gravity, commission)
            offers.append({
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": gravity,
                "url": url,
                "viral_score": viral_score,
            })
        except Exception as e:
            logger.warning(f"Skipping offer due to parse error: {e}")
            continue

    # Sort by viral score descending
    offers.sort(key=lambda x: x["viral_score"], reverse=True)
    return offers

def calculate_viral_score(gravity, commission):
    try:
        gravity_val = float(gravity)
        commission_val = float(commission.strip('%').replace('$', ''))
        score = gravity_val * commission_val
        return score
    except Exception:
        return 0

async def scrape_clickbank_top_offers():
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, CLICKBANK_TOP_OFFERS_URL)
        if not html:
            return []
        offers = parse_offers(html)
        return offers


if __name__ == "__main__":
    offers = asyncio.run(scrape_clickbank_top_offers())
    for offer in offers[:10]:
        print(f"{offer['name']} | Price: {offer['price']} | Commission: {offer['commission']} | Viral Score: {offer['viral_score']}")
