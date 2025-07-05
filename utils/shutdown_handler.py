import signal
import sys
import logging

def setup_shutdown_handler(cleanup_func):
    def handler(signum, frame):
        logging.info("Shutdown signal received, cleaning up...")
        cleanup_func()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
