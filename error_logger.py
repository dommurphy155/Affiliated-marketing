from utils.error_logger import log_error

try:
    # risky code
except Exception as e:
    log_error(e)
    raise  # or handle
