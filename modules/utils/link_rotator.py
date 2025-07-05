import random

AFFILIATE_LINKS = [
    "https://hop.clickbank.net/?affiliate=digiprof25&vendor=product1",
    "https://hop.clickbank.net/?affiliate=digiprof25&vendor=product2",
    "https://hop.clickbank.net/?affiliate=digiprof25&vendor=product3",
]

def get_random_link():
    return random.choice(AFFILIATE_LINKS)
