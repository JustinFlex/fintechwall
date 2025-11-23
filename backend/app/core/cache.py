"""Redis cache helpers for snapshot storage."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .settings import settings


class CacheManager:
    """Cache manager for market data with Redis backend."""

    def __init__(self, url: Optional[str] = None) -> None:
        self._pool = None
        self._enabled = False

        if REDIS_AVAILABLE and settings.redis_enabled and url:
            try:
                self._pool = redis.from_url(url, decode_responses=True)
                self._enabled = True
            except Exception:
                self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._pool is not None

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self.enabled:
            return None
        try:
            return await self._pool.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set key-value pair with TTL."""
        if not self.enabled:
            return False
        try:
            await self._pool.set(key, value, ex=ttl)
            return True
        except Exception:
            return False

    async def get_json(self, key: str) -> Optional[dict[str, Any]]:
        """Get JSON value by key."""
        if not self.enabled:
            return None
        try:
            raw = await self._pool.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def set_json(self, key: str, payload: Mapping[str, Any], ttl: int = 300) -> bool:
        """Set JSON value with TTL."""
        if not self.enabled:
            return False
        try:
            await self._pool.set(key, json.dumps(payload, default=str), ex=ttl)
            return True
        except Exception:
            return False


class CacheClient(CacheManager):
    """Legacy alias for CacheManager - for backward compatibility."""
    pass


# Create default cache instance
cache = CacheManager(settings.redis_url if hasattr(settings, 'redis_url') else None)
