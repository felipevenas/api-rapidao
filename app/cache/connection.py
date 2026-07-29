from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """Inicializa o pool de conexões com o Redis de forma assíncrona."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    """Encerra a conexão com o Redis se ativa."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Injetor de dependência do cliente Redis para endpoints do FastAPI."""
    global redis_client
    if redis_client is None:
        redis_client = await init_redis()
    yield redis_client
