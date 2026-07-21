from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException


class InMemoryRateLimiter:
    """Per-process throttling for the single-instance MVP.

    The deployment remains a single FastAPI process in the MVP. A shared limiter is
    deliberately deferred until the approved deployment topology changes.
    """

    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int = 60) -> None:
        now = monotonic()
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= now - window_seconds:
                attempts.popleft()
            if len(attempts) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "rate_limited",
                        "message": "Too many requests. Try again shortly.",
                    },
                    headers={"Retry-After": str(window_seconds)},
                )
            attempts.append(now)


auth_rate_limiter = InMemoryRateLimiter()
search_rate_limiter = InMemoryRateLimiter()
