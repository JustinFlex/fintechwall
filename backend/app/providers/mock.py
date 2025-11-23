"""Mock data provider for offline/local development."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping

from .base import MarketDataProvider


class MockProvider(MarketDataProvider):
    """Provides deterministic mock data that matches the unified snapshot schema."""

    def __init__(self) -> None:
        self.now = datetime.now()

    def _ts(self) -> str:
        return (self.now + timedelta(seconds=0)).isoformat()

    async def fetch_indices(self) -> Mapping[str, Any]:
        """Return a mix of A-share和全球指数的快照。"""
        return {
            "000001.SH": {"name": "上证综指", "display_name": "上证综指", "last": 3150.2, "change": -12.3, "change_pct": -0.39, "prev_close": 3162.5, "timestamp": self._ts()},
            "399001.SZ": {"name": "深证成指", "display_name": "深证成指", "last": 11230.4, "change": 45.6, "change_pct": 0.41, "prev_close": 11184.8, "timestamp": self._ts()},
            "000300.SH": {"name": "沪深300", "display_name": "沪深300", "last": 4188.7, "change": -8.4, "change_pct": -0.20, "prev_close": 4197.1, "timestamp": self._ts()},
            "000852.SH": {"name": "中证1000", "display_name": "中证1000", "last": 7205.3, "change": 35.2, "change_pct": 0.49, "prev_close": 7170.1, "timestamp": self._ts()},
            "000016.SH": {"name": "上证50", "display_name": "上证50", "last": 2852.1, "change": -5.6, "change_pct": -0.20, "prev_close": 2857.7, "timestamp": self._ts()},
            "000905.SH": {"name": "中证500", "display_name": "中证500", "last": 6120.4, "change": 28.7, "change_pct": 0.47, "prev_close": 6091.7, "timestamp": self._ts()},
            "SPX.GI": {"name": "标普500", "display_name": "标普500", "last": 5235.4, "change": 12.1, "change_pct": 0.23, "prev_close": 5223.3, "timestamp": self._ts()},
            "NDXTMC.GI": {"name": "纳指100等权", "display_name": "纳指100等权", "last": 2233.2, "change": -5.4, "change_pct": -0.24, "prev_close": 2238.6, "timestamp": self._ts()},
            "HSI.HI": {"name": "恒生指数", "display_name": "恒生指数", "last": 18230.5, "change": 86.2, "change_pct": 0.48, "prev_close": 18144.3, "timestamp": self._ts()},
            "SX5E.GI": {"name": "欧元区50", "display_name": "欧元区50", "last": 4850.4, "change": -15.2, "change_pct": -0.31, "prev_close": 4865.6, "timestamp": self._ts()},
            "UKX.GI": {"name": "富时100", "display_name": "富时100", "last": 7950.3, "change": 22.4, "change_pct": 0.28, "prev_close": 7927.9, "timestamp": self._ts()},
            "CAC.GI": {"name": "法国CAC40", "display_name": "法国CAC40", "last": 7288.1, "change": -12.6, "change_pct": -0.17, "prev_close": 7300.7, "timestamp": self._ts()},
            "DAX.GI": {"name": "德国DAX", "display_name": "德国DAX", "last": 18750.8, "change": 65.1, "change_pct": 0.35, "prev_close": 18685.7, "timestamp": self._ts()},
        }

    async def fetch_fx(self) -> Mapping[str, Any]:
        return {
            "USDCNH.FX": {"last": 7.1123, "change": -0.0045, "change_pct": -0.06, "timestamp": self._ts()},
            "EURUSD.FX": {"last": 1.0812, "change": 0.0008, "change_pct": 0.07, "timestamp": self._ts()},
            "USDJPY.FX": {"last": 157.12, "change": -0.42, "change_pct": -0.27, "timestamp": self._ts()},
            "USDX.FX": {"last": 100.25, "change": 0.05, "change_pct": 0.05, "timestamp": self._ts()},
        }

    async def fetch_rates(self) -> Mapping[str, Any]:
        """Return简化的利率/收益率点位."""
        return {
            "M0000017.SH": {"name": "中国国债10Y", "last": 2.69, "change": -0.01, "timestamp": self._ts()},
            "M0000025.SH": {"name": "中国国债5Y", "last": 2.48, "change": 0.00, "timestamp": self._ts()},
            "M0000007.SH": {"name": "中国国债3Y", "last": 2.32, "change": 0.00, "timestamp": self._ts()},
            "UST10Y.GBM": {"name": "美国国债10Y", "last": 3.98, "change": 0.02, "timestamp": self._ts()},
            "UST2Y.GBM": {"name": "美国国债2Y", "last": 4.32, "change": 0.01, "timestamp": self._ts()},
            "LPR1Y.IR": {"name": "LPR 1Y", "last": 3.45, "change": 0.00, "timestamp": self._ts()},
            "LPR5Y.IR": {"name": "LPR 5Y", "last": 3.95, "change": 0.00, "timestamp": self._ts()},
        }

    async def fetch_commodities(self) -> Mapping[str, Any]:
        return {
            "GC.CMX": {"name": "COMEX Gold", "last": 4067.1, "change": 7.1, "change_pct": 0.17, "volume": 128464, "timestamp": self._ts()},
            "CL.NYM": {"name": "NYMEX Crude", "last": 58.35, "change": -0.65, "change_pct": -1.10, "volume": 127165, "timestamp": self._ts()},
            "TA.CZC": {"name": "PTA 主力", "last": 4642, "change": -36, "change_pct": -0.77, "volume": 161257, "timestamp": self._ts()},
            "RB.SHF": {"name": "螺纹钢 主力", "last": 3054, "change": -6, "change_pct": -0.20, "volume": 129603, "timestamp": self._ts()},
            "HG.CMX": {"name": "COMEX Copper", "last": 4.9745, "change": 0.006, "change_pct": 0.12, "volume": 20788, "timestamp": self._ts()},
        }

    async def fetch_us_stocks(self) -> Mapping[str, Any]:
        return {
            "DJI.GI": {"name": "道琼斯", "last": 38500.2, "change": 85.3, "change_pct": 0.22, "timestamp": self._ts()},
            "SPX.GI": {"name": "标普500", "last": 5235.4, "change": 12.1, "change_pct": 0.23, "timestamp": self._ts()},
            "IXIC.GI": {"name": "纳斯达克", "last": 15980.6, "change": -42.8, "change_pct": -0.27, "timestamp": self._ts()},
            "AAPL.O": {"name": "苹果", "last": 188.2, "change": 1.2, "change_pct": 0.64, "timestamp": self._ts()},
            "MSFT.O": {"name": "微软", "last": 332.5, "change": 0.8, "change_pct": 0.24, "timestamp": self._ts()},
        }

    async def fetch_crypto(self) -> Mapping[str, Any]:
        return {
            "BTC.CC": {"name": "比特币", "last": 63000, "change_pct": 1.2, "change": 750, "timestamp": self._ts()},
            "ETH.CC": {"name": "以太坊", "last": 3100, "change_pct": -0.8, "change": -25, "timestamp": self._ts()},
            "SOL.CC": {"name": "Solana", "last": 155, "change_pct": 3.4, "change": 5.2, "timestamp": self._ts()},
            "DOGE.CC": {"name": "Dogecoin", "last": 0.17, "change_pct": -1.1, "change": -0.002, "timestamp": self._ts()},
        }

    async def fetch_calendar(self) -> list[Mapping[str, Any]]:
        now = datetime.utcnow()
        return [
            {
                "event_id": "NFP",
                "title": "美国非农就业",
                "country": "US",
                "datetime": (now + timedelta(days=2)).isoformat() + "Z",
                "importance": "high",
                "consensus": "200k",
                "previous": "210k",
            },
            {
                "event_id": "CPI_CN",
                "title": "中国CPI同比",
                "country": "CN",
                "datetime": (now + timedelta(days=3)).isoformat() + "Z",
                "importance": "medium",
                "consensus": "0.8%",
                "previous": "0.6%",
            },
        ]

    async def fetch_a_share_short_term(self) -> Mapping[str, Any]:
        timestamp = self._ts()
        boards = [
            {
                "code": "BK0470",
                "name": "半导体",
                "change_pct": 2.8,
                "net_flow": 12.5,
            },
            {
                "code": "BK0428",
                "name": "算力",
                "change_pct": 1.9,
                "net_flow": 9.4,
            },
            {
                "code": "BK0600",
                "name": "券商",
                "change_pct": 1.1,
                "net_flow": 5.3,
            },
            {
                "code": "BK0804",
                "name": "新能源车",
                "change_pct": -0.6,
                "net_flow": -2.1,
            },
            {
                "code": "BK0491",
                "name": "光伏",
                "change_pct": -1.4,
                "net_flow": -3.8,
            },
        ]
        hot = sorted(boards, key=lambda x: x["change_pct"], reverse=True)
        cold = sorted(boards, key=lambda x: x["change_pct"])
        flow = sorted(boards, key=lambda x: x["net_flow"], reverse=True)
        return {
            "timestamp": timestamp,
            "source": "mock",
            "hot_boards": hot[:4],
            "cold_boards": cold[:4],
            "capital_boards": flow[:4],
        }
