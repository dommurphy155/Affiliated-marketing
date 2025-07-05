import json, os

CACHE_FILE = "cache/products.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def is_cached(product_id):
    cache = load_cache()
    return product_id in cache

def add_to_cache(product_id):
    cache = load_cache()
    if product_id not in cache:
        cache.append(product_id)
        save_cache(cache)p
