import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs to scrape — public top product pages (no login)
URLS = {
    "clickbank": "https://www.clickbank.com/top-marketplaces/",  # Confirm exact top offers URL as needed
    "jvzoo": "https://www.jvzoo.com/marketplace",  # JVZoo marketplace front
    "warriorplus": "https://www.warriorplus.com/marketplace",  # WarriorPlus marketplace
    "shareasale": "https://www.shareasale.com/shareasale.cfm?merchantID=0",  # public merchant list
    "clickfunnels": "https://marketplace.clickfunnels.com/",  # Clickfunnels marketplace
    "amazon_uk": "https://www.amazon.co.uk/gp/bestsellers",  # Amazon UK Best Sellers landing page
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36"
}


async def fetch_html(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""


def parse_clickbank(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")

    # This page structure might change; adapt selectors accordingly
    rows = soup.select("table.marketplace-table tr")[1:]  # skip header
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        try:
            name = cols[0].get_text(strip=True)
            url = cols[0].find("a")["href"] if cols[0].find("a") else ""
            price = cols[1].get_text(strip=True)
            commission = cols[2].get_text(strip=True)
            gravity = cols[3].get_text(strip=True)
            viral_score = calculate_viral_score(gravity, commission)
            offers.append({
                "marketplace": "ClickBank",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": gravity,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"ClickBank parse error: {e}")
            continue
    return offers


def parse_jvzoo(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".productListItem")  # Check selector in case it changes

    for prod in products:
        try:
            name = prod.select_one(".productTitle").get_text(strip=True)
            url = prod.select_one("a")["href"]
            price = prod.select_one(".productPrice").get_text(strip=True)
            commission = prod.select_one(".commission").get_text(strip=True) if prod.select_one(".commission") else "0"
            viral_score = calculate_viral_score("1", commission)  # JVZoo no gravity, so fake 1
            offers.append({
                "marketplace": "JVZoo",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": None,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"JVZoo parse error: {e}")
            continue
    return offers


def parse_warriorplus(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".product-card")  # Adjust selector if needed

    for prod in products:
        try:
            name = prod.select_one(".product-title").get_text(strip=True)
            url = prod.select_one("a")["href"]
            price = prod.select_one(".price").get_text(strip=True)
            commission = prod.select_one(".commission").get_text(strip=True) if prod.select_one(".commission") else "0"
            viral_score = calculate_viral_score("1", commission)
            offers.append({
                "marketplace": "WarriorPlus",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": None,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"WarriorPlus parse error: {e}")
            continue
    return offers


def parse_shareasale(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table#merchantlist tr")[1:]  # skip header

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue
        try:
            name = cols[0].get_text(strip=True)
            url = cols[0].find("a")["href"] if cols[0].find("a") else ""
            price = "N/A"  # ShareASale does not list price openly here
            commission = cols[3].get_text(strip=True)
            viral_score = calculate_viral_score("1", commission)
            offers.append({
                "marketplace": "ShareASale",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": None,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"ShareASale parse error: {e}")
            continue
    return offers


def parse_clickfunnels(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".marketplace-product")

    for prod in products:
        try:
            name = prod.select_one(".product-name").get_text(strip=True)
            url = prod.select_one("a")["href"]
            price = prod.select_one(".price").get_text(strip=True)
            commission = prod.select_one(".commission").get_text(strip=True) if prod.select_one(".commission") else "0"
            viral_score = calculate_viral_score("1", commission)
            offers.append({
                "marketplace": "ClickFunnels",
                "name": name,
                "price": price,
                "commission": commission,
                "gravity": None,
                "url": url,
                "viral_score": viral_score
            })
        except Exception as e:
            logger.warning(f"ClickFunnels parse error: {e}")
            continue
    return offers


def parse_amazon_uk(html):
    offers = []
    soup = BeautifulSoup(html, "html.parser")

    # Amazon Best Sellers category blocks
    items = soup.select("div.p13n-desktop-grid") or soup.select("div.zg-grid-general-faceout")
    if not items:
        logger.warning("Amazon UK best sellers page layout not recognized.")
        return offers

    # Attempt to parse individual items
    products = soup.select("div.zg-item-immersion")
    if not products:
        # fallback grid items
        products = soup.select("div.a-section.a-spacing-none.aok-relative")

    for prod in products[:20]:  # limit to top 20
        try:
            name = prod.select_one("div.p13n-sc-truncate, span.a-text-normal")
            name_text = name.get_text(strip=True) if name else "N/A"
            url = prod.select_one("a.a-link-normal")["href"] if prod.select_one("a.a-link-normal") else ""
            if url and not url.startswith("http"):
                url = "https://www.amazon.co.uk" + url
            price = prod.select_one("span.p13n-sc-price") or prod.select_one("span.a-price-whole")
            price_text = price.get_text(strip=True) if price else "N/A"
            offers.append({
                "marketplace": "Amazon UK",
                "name": name_text,
                "price": price_text,
                "commission": "N/A",
                "gravity": None,
                "url": url,
                "viral_score": 0  # No viral score on Amazon
            })
        except Exception as e:
            logger.warning(f"Amazon UK parse error: {e}")
            continue
    return offers


def calculate_viral_score(gravity, commission):
    try:
        gravity_val = float(gravity)
        commission_clean = commission.replace('%', '').replace('$', '').replace('£', '').strip()
        commission_val = float(commission_clean) if commission_clean else 0
        return gravity_val * commission_val
    except Exception:
        return 0


async def scrape_clickbank_top_offers(session):
    html = await fetch_html(session, URLS["clickbank"])
    if not html:
        return []
    return parse_clickbank(html)


async def scrape_jvzoo_offers(session):
    html = await fetch_html(session, URLS["jvzoo"])
    if not html:
        return []
    return parse_jvzoo(html)


async def scrape_warriorplus_offers(session):
    html = await fetch_html(session, URLS["warriorplus"])
    if not html:
        return []
    return parse_warriorplus(html)


async def scrape_shareasale_offers(session):
    html = await fetch_html(session, URLS["shareasale"])
    if not html:
        return []
    return parse_shareasale(html)


async def scrape_clickfunnels_offers(session):
    html = await fetch_html(session, URLS["clickfunnels"])
    if not html:
        return []
    return parse_clickfunnels(html)


async def scrape_amazon_uk_offers(session):
    html = await fetch_html(session, URLS["amazon_uk"])
    if not html:
        return []
    return parse_amazon_uk(html)


async def scrape_all():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            scrape_clickbank_top_offers(session),
            scrape_jvzoo_offers(session),
            scrape_warriorplus_offers(session),
            scrape_shareasale_offers(session),
            scrape_clickfunnels_offers(session),
            scrape_amazon_uk_offers(session),
            return_exceptions=True,
        )
    combined = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Error in scraping task: {r}")
            continue
        combined.extend(r)
    # Sort combined list by viral_score descending
    combined.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
    return combined


if __name__ == "__main__":
    import pprint
    offers = asyncio.run(scrape_all())
    pprint.pprint(offers[:20])
