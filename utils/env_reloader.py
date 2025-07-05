import os
import logging
from dotenv import load_dotenv

def reload_env():
    load_dotenv()
    logging.info("Environment variables reloaded")
