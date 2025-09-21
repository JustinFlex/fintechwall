"""Redis cache helpers for snapshot storage."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

import redis.asyncio as redis

from .settings import settings


class CacheClient:
    """Thin wrapper around Redis for JSON payload caching."""

    def __init__(self, url: str) -> None:
        self._pool = redis.from_url(url, decode_responses=True) if settings.redis_enabled else None

    @property
    def enabled(self) -> bool:
        return self._pool is not None

    async def get_json(self, key: str) -> Optional[dict[str, Any]]:
        if not self.enabled:
            return None
        raw = await self._pool.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, payload: Mapping[str, Any], ttl: int) -> None:
        if not self.enabled:
            return
        await self._pool.set(key, json.dumps(payload), ex=ttl)


cache = CacheClient(settings.redis_url)
