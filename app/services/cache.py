import json
from typing import Any

from app.core.redis import get_redis


CACHE_PREFIX = "clevia:v1"


def cache_key(*parts: object) -> str:
    cleaned = [str(part).strip().lower() for part in parts]
    return ":".join([CACHE_PREFIX, *cleaned])


async def cache_get_json(key: str) -> Any | None:
    redis = get_redis()
    value = await redis.get(key)
    if value is None:
        return None
    return json.loads(value)


async def cache_set_json(
    key: str,
    value: Any,
    ttl_seconds: int,
) -> None:
    redis = get_redis()
    await redis.set(
        key,
        json.dumps(value, ensure_ascii=False, default=str),
        ex=ttl_seconds,
    )


async def cache_delete(key: str) -> None:
    redis = get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> int:
    redis = get_redis()
    deleted = 0
    batch: list[str] = []

    async for key in redis.scan_iter(match=pattern, count=100):
        batch.append(key)
        if len(batch) >= 100:
            deleted += await redis.delete(*batch)
            batch.clear()

    if batch:
        deleted += await redis.delete(*batch)

    return deleted
