from collections import defaultdict
import time

class FloodProtector:
    def __init__(self, limit=5, interval=10):
        self.limit = limit
        self.interval = interval
        self.users = defaultdict(list)

    def is_allowed(self, user_id):
        now = time.time()
        timestamps = self.users[user_id]
        # Remove timestamps older than interval
        self.users[user_id] = [t for t in timestamps if now - t < self.interval]
        if len(self.users[user_id]) >= self.limit:
            return False
        self.users[user_id].append(now)
        return True
