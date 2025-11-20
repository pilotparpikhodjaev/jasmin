import time
from typing import Protocol

from redis.asyncio import Redis

from .exceptions import RateLimitExceeded


class RateLimiter:
    def __init__(self, redis: Redis, window_seconds: int = 1):
        self._redis = redis
        self._window = window_seconds

    async def check(self, account_id: str, limit: int) -> None:
        if limit <= 0:
            return

        bucket = int(time.time() / self._window)
        key = f"rate:{account_id}:{bucket}"
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, self._window)
        if count > limit:
            raise RateLimitExceeded(f"Rate limit exceeded ({limit} req/s)")

