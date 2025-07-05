import json, os

CACHE_FILE = "cache/products.json"

def ensure_cache_dir():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

def get_all_cached_products():
    ensure_cache_dir()
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def cache_product(product: dict):
    ensure_cache_dir()
    data = get_all_cached_products()
    data.insert(0, product)
    with open(CACHE_FILE, "w") as f:
        json.dump(data[:20], f, indent=2)  # limit to 20 entries
