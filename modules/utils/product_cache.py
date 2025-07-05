
import os
import json
import logging

# Path to your cache file
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "products.json")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def load_cache():
    """Loads the cache from file safely."""
    if not os.path.exists(CACHE_FILE):
        logging.warning("Cache file not found. Returning empty list.")
        return []

    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error reading cache file: {e}")
        return []

def save_cache(data):
    """Saves data to the cache file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logging.error(f"Failed to write to cache file: {e}")

def get_all_cached_products():
    """Returns all cached products or empty list with failsafe."""
    return load_cache()
