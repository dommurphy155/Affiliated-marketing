import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.calls = defaultdict(list)
        self.max_calls = max_calls
        self.period = period

    def allow(self, user_id):
        now = time.time()
        self.calls[user_id] = [t for t in self.calls[user_id] if now - t < self.period]
        if len(self.calls[user_id]) >= self.max_calls:
            return False
        self.calls[user_id].append(now)
        return True
