import psutil, logging

def check_memory(threshold_mb=150):
    process = psutil.Process()
    mem = process.memory_info().rss / 1024 / 1024
    if mem > threshold_mb:
        logging.warning(f"⚠️ Memory usage high: {mem:.2f} MB")
