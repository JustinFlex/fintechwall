"""Provider abstractions for market data ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class MarketDataProvider(ABC):
    """Contract all data providers must follow regardless of source."""

    @abstractmethod
    async def fetch_indices(self) -> Mapping[str, Any]:
        """Return a snapshot of index data keyed by canonical ticker."""

    @abstractmethod
    async def fetch_fx(self) -> Mapping[str, Any]:
        """Return FX snapshot payload."""

    @abstractmethod
    async def fetch_rates(self) -> Mapping[str, Any]:
        """Return rates and yield data."""

    @abstractmethod
    async def fetch_commodities(self) -> Mapping[str, Any]:
        """Return commodities snapshot (energy/metals)."""

    @abstractmethod
    async def fetch_crypto(self) -> Mapping[str, Any]:
        """Return crypto spot + derivatives summary."""

    @abstractmethod
    async def fetch_calendar(self) -> list[Mapping[str, Any]]:
        """Return upcoming economic events."""


class NullProvider(MarketDataProvider):
    """Placeholder provider until real integrations are implemented."""

    async def fetch_indices(self) -> Mapping[str, Any]:
        return {}

    async def fetch_fx(self) -> Mapping[str, Any]:
        return {}

    async def fetch_rates(self) -> Mapping[str, Any]:
        return {}

    async def fetch_commodities(self) -> Mapping[str, Any]:
        return {}

    async def fetch_crypto(self) -> Mapping[str, Any]:
        return {}

    async def fetch_calendar(self) -> list[Mapping[str, Any]]:
        return []
