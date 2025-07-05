import logging

def try_or_log(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logging.error(f"Failsafe triggered in {fn.__name__}: {e}")
    return wrapper
