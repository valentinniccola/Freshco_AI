import time
from typing import Dict, List
from fastapi import HTTPException, status

class RateLimiter:
    """
    Sliding window in-memory rate limiter per user.
    Default: max 20 uploads per 10 minutes (600 seconds).
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # user_id -> list of timestamps
        self._user_requests: Dict[str, List[float]] = {}

    def check_rate_limit(self, user_key: str):
        now = time.time()
        window_start = now - self.window_seconds

        if user_key not in self._user_requests:
            self._user_requests[user_key] = []

        # Filter out requests older than the rolling window
        valid_requests = [t for t in self._user_requests[user_key] if t > window_start]
        self._user_requests[user_key] = valid_requests

        if len(valid_requests) >= self.max_requests:
            retry_after_seconds = int(valid_requests[0] - window_start) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Upload limit reached (max {self.max_requests} uploads per 10 minutes). Please wait {max(1, retry_after_seconds // 60)} minute(s) before trying again.",
                headers={"Retry-After": str(retry_after_seconds)}
            )

        # Record current request timestamp
        self._user_requests[user_key].append(now)

# Global Rate Limiter Instance (20 requests per 10 minutes)
upload_rate_limiter = RateLimiter(max_requests=20, window_seconds=600)
