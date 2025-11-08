from dataclasses import dataclass

from redis.asyncio import Redis


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int


class RateLimiter:
    """Redis-backed fixed window rate limiter."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window_seconds)

        allowed = current <= limit
        remaining = max(limit - current, 0)
        return RateLimitResult(allowed=allowed, remaining=remaining)
