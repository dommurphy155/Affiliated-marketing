import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text):
    return text.strip().replace('\n', ' ').replace('\r', '').replace('  ', ' ')


def calculate_viral_score(gravity: float = 1.0, commission: float = 1.0):
    try:
        return float(gravity) * float(commission)
    except:
        return 0


async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as resp:
            if resp.status != 200:
                logger.warning(f"Non-200 from {url}")
                return ""
            return await resp.text()
    except Exception as e:
        logger.warning(f"Fetch error from {url}: {e}")
        return ""


# 1. ClickBank
async def scrape_clickbank(session):
    url = "https://www.clickbank.com/marketplace"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for offer in soup.select("div.card")[:10]:
        try:
            name = clean_text(offer.select_one(".product-title").text)
            commission = clean_text(offer.select_one(".commission").text).replace("%", "").replace("$", "")
            gravity = "1.0"  # Fallback for viral score
            link = offer.select_one("a")["href"]
            results.append({
                "name": name,
                "price": "N/A",
                "commission": commission,
                "gravity": gravity,
                "url": link,
                "source": "ClickBank",
                "viral_score": calculate_viral_score(gravity, commission)
            })
        except Exception:
            continue

    return results


# 2. Amazon UK – Best Sellers
async def scrape_amazon(session):
    url = "https://www.amazon.co.uk/gp/bestsellers"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for li in soup.select("div.zg-grid-general-faceout")[:10]:
        try:
            title = clean_text(li.select_one(".p13n-sc-truncated").text)
            link = "https://www.amazon.co.uk" + li.select_one("a")["href"]
            results.append({
                "name": title,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "1.0",
                "url": link,
                "source": "Amazon UK",
                "viral_score": 1.0
            })
        except Exception:
            continue

    return results


# 3. eBay
async def scrape_ebay(session):
    url = "https://www.ebay.co.uk/deals"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for li in soup.select("div.ebayui-dne-item-featured-card")[:10]:
        try:
            name = clean_text(li.select_one("h3").text)
            link = li.select_one("a")["href"]
            results.append({
                "name": name,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "1.0",
                "url": link,
                "source": "eBay",
                "viral_score": 1.0
            })
        except Exception:
            continue

    return results


# 4. Etsy
async def scrape_etsy(session):
    url = "https://www.etsy.com/uk/c/trending"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for item in soup.select("li.wt-list-unstyled")[:10]:
        try:
            link_el = item.select_one("a")
            title = clean_text(link_el.text)
            link = link_el["href"]
            results.append({
                "name": title,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "1.0",
                "url": link,
                "source": "Etsy",
                "viral_score": 1.0
            })
        except Exception:
            continue

    return results


# 5. JVZoo
async def scrape_jvzoo(session):
    url = "https://www.jvzoo.com/"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for tr in soup.select("table tr")[1:11]:
        try:
            cols = tr.find_all("td")
            if len(cols) < 2:
                continue
            name = clean_text(cols[0].text)
            results.append({
                "name": name,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "1.0",
                "url": "https://www.jvzoo.com/",
                "source": "JVZoo",
                "viral_score": 1.0
            })
        except Exception:
            continue

    return results


# 6. WarriorPlus
async def scrape_warriorplus(session):
    url = "https://warriorplus.com/deal-of-the-day"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for offer in soup.select("div.warrior-offer")[:10]:
        try:
            name = clean_text(offer.select_one("h2").text)
            link = offer.select_one("a")["href"]
            results.append({
                "name": name,
                "price": "N/A",
                "commission": "N/A",
                "gravity": "1.0",
                "url": link,
                "source": "WarriorPlus",
                "viral_score": 1.0
            })
        except Exception:
            continue

    return results


# Combine all
async def scrape_all() -> List[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [
            scrape_clickbank(session),
            scrape_amazon(session),
            scrape_ebay(session),
            scrape_etsy(session),
            scrape_jvzoo(session),
            scrape_warriorplus(session)
        ]
        results = await asyncio.gather(*tasks)
        all_products = [item for sublist in results for item in sublist]
        return sorted(all_products, key=lambda x: x["viral_score"], reverse=True)


if __name__ == "__main__":
    results = asyncio.run(scrape_all())
    for r in results[:10]:
        print(f"{r['source']} | {r['name']} | {r['url']}")
