import time
from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis
from app.core.config import settings
from app.cache import redis_client, init_redis


class SlidingWindowRateLimiter:
    """Implementação do algoritmo Sliding Window utilizando Redis ZSET."""

    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    async def is_rate_limited(self, redis: aioredis.Redis, identifier: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_seconds
        key = f"rate_limit:{identifier}"

        try:
            async with redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {f"{current_time}": current_time})
                pipe.zcard(key)
                pipe.expire(key, self.window_seconds + 5)
                results = await pipe.execute()

            request_count = results[2]
            return request_count > self.requests_limit
        except Exception:
            return False


async def rate_limit_check(
    request: Request,
    requests_limit: int = settings.RATE_LIMIT_DEFAULT_REQUESTS,
    window_seconds: int = settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
):
    """Dependência do FastAPI para verificação de rate limit em rotas sensíveis."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = await init_redis()
        except Exception:
            return

    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    identifier = auth_header if auth_header else f"ip:{client_ip}:{request.url.path}"

    limiter = SlidingWindowRateLimiter(requests_limit, window_seconds)
    limited = await limiter.is_rate_limited(redis_client, identifier)

    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "status": "error",
                "message": "Limite de requisições excedido. Tente novamente mais tarde.",
                "details": {"window_seconds": window_seconds, "limit": requests_limit},
            },
        )
