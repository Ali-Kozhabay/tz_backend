from collections.abc import Callable

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import get_settings

_sync_instance: SyncRedis | None = None
_async_instance: AsyncRedis | None = None
_async_factory: Callable[[], AsyncRedis] | None = None


def get_redis() -> SyncRedis:
    global _sync_instance
    if _sync_instance is None:
        settings = get_settings()
        _sync_instance = SyncRedis.from_url(settings.redis_url, decode_responses=True)
    return _sync_instance


def get_async_redis() -> AsyncRedis:
    global _async_instance, _async_factory
    if _async_instance is None:
        if _async_factory is not None:
            return _async_factory()
        settings = get_settings()
        _async_instance = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    return _async_instance


def override_redis(
    sync_client: SyncRedis | None,
    async_client: AsyncRedis | Callable[[], AsyncRedis] | None,
) -> None:
    global _sync_instance, _async_instance, _async_factory
    if sync_client is not None:
        _sync_instance = sync_client
    if async_client is not None:
        if callable(async_client):
            _async_factory = async_client
            _async_instance = None
        else:
            _async_instance = async_client
            _async_factory = None
