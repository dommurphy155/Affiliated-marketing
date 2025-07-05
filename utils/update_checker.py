import subprocess
import logging

def check_for_updates():
    result = subprocess.run(["git", "fetch"], capture_output=True)
    local = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True).stdout.strip()
    remote = subprocess.run(["git", "rev-parse", "@{u}"], capture_output=True).stdout.strip()
    if local != remote:
        logging.info("Updates available")
        return True
    logging.info("No updates found")
    return False
