from scraper import scrape_clickbank_top_offers

def get_affiliate_links():
    offers = scrape_clickbank_top_offers()
    formatted = []
    for offer in offers:
        formatted.append({
            "title": offer['title'],
            "link": f"https://hop.clickbank.net/?affiliate={os.getenv('CLICKBANK_NICKNAME')}&vendor={offer['url']}"
        })
    return formatted
