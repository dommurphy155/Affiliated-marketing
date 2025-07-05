import time, threading, logging

def start_heartbeat(interval=300):
    def beat():
        while True:
            logging.info("✅ Heartbeat: Bot alive and running.")
            time.sleep(interval)
    threading.Thread(target=beat, daemon=True).start()
