import requests
from bs4 import BeautifulSoup

def scrape_clickbank_top_offers():
    url = "https://www.clickbank.com/marketplace/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    offers = []
    for product in soup.select(".product"):
        title = product.select_one(".product-title")
        link = product.select_one("a")["href"]
        if title and link:
            offers.append({
                "title": title.text.strip(),
                "url": link
            })
    return offers[:17]  # Return top 17 offers
