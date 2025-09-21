"""High-level data orchestration layer."""

from __future__ import annotations

from typing import Any, Mapping

from ..core.cache import cache
from ..core.settings import settings
from ..providers.base import NullProvider, MarketDataProvider


class DataService:
    """Retrieve market data snapshots using the configured provider."""

    def __init__(self, provider: MarketDataProvider | None = None) -> None:
        self.provider = provider or NullProvider()
        self.cache_enabled = cache.enabled and settings.snapshot_cache_ttl > 0
        self.cache_key = f"wallboard:snapshot:{settings.data_mode}"

    async def snapshot(self) -> Mapping[str, Any]:
        if self.cache_enabled:
            cached = await cache.get_json(self.cache_key)
            if cached:
                return cached

        indices = await self.provider.fetch_indices()
        fx = await self.provider.fetch_fx()
        rates = await self.provider.fetch_rates()
        commodities = await self.provider.fetch_commodities()
        crypto = await self.provider.fetch_crypto()
        calendar = await self.provider.fetch_calendar()

        payload = {
            "metadata": {
                "data_mode": settings.data_mode,
            },
            "indices": indices,
            "fx": fx,
            "rates": rates,
            "commodities": commodities,
            "crypto": crypto,
            "calendar": calendar,
        }

        if self.cache_enabled:
            await cache.set_json(self.cache_key, payload, settings.snapshot_cache_ttl)

        return payload
