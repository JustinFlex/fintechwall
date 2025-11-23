"""Wind data provider implementation for A-share market data."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Mapping
import math

from .base import MarketDataProvider
from .mock import MockProvider

logger = logging.getLogger(__name__)


class WindProvider(MarketDataProvider):
    """Wind API provider for Chinese A-share market data."""

    # Core code buckets, aligned with docs/api_specs/wind and data-api-requirements
    INDEX_CODES = [
        # A-share core
        "000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000852.SH", "000016.SH", "932000.CSI", "899050.BJ",
        # Global
        "SPX.GI", "IXIC.GI", "NDXTMC.GI", "DJI.GI", "HSI.HI", "N225.GI", "FTSE.GI", "GDAXI.GI", "RTSI.GI",
    ]
    FX_CODES = [
        "USDCNY.IB", "USDCNH.FX", "USDX.FX", "EURUSD.FX", "USDJPY.FX", "GBPUSD.FX",
        "USDCAD.FX", "AUDUSD.FX", "NZDUSD.FX", "USDCHF.FX",
    ]
    POLICY_RATE_CODES = ["LPR1Y.IR", "LPR5Y.IR", "SHIBORON.IR", "SHIBOR1W.IR", "SHIBOR1M.IR", "SHIBOR3M.IR", "SHIBOR1Y.IR"]
    GOVY_CN_CODES = ["TB1Y.WI", "TB3Y.WI", "TB5Y.WI", "TB7Y.WI", "TB10Y.WI"]
    GOVY_US_CODES = ["UST2Y.GBM", "UST5Y.GBM", "UST10Y.GBM", "UST30Y.GBM"]
    COMMODITY_CODES = [
        "GC.CMX", "SI.CMX", "HG.CMX", "ALI.CMX", "CL.NYM", "PL.NYM", "NG.NYM",
        "TA.CZC", "J.DCE", "SA.CZC", "S.CBT", "C.CBT", "W.CBT", "ZE.CBT", "LH.DCE", "RB.SHF",
    ]

    NAME_MAP = {
        "000001.SH": "上证综指",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
        "000300.SH": "沪深300",
        "000852.SH": "中证1000",
        "000016.SH": "上证50",
        "932000.CSI": "中证全指金融",
        "899050.BJ": "北证50",
        "SPX.GI": "标普500",
        "IXIC.GI": "纳斯达克综合",
        "NDXTMC.GI": "纳指100等权",
        "DJI.GI": "道琼斯",
        "HSI.HI": "恒生指数",
        "N225.GI": "日经225",
        "FTSE.GI": "富时100",
        "GDAXI.GI": "德国DAX",
        "RTSI.GI": "俄罗斯RTS",
        "USDX.FX": "美元指数",
    }

    COMMODITY_SECTOR = {
        "GC.CMX": "PreciousMetals",
        "SI.CMX": "PreciousMetals",
        "PL.NYM": "PreciousMetals",
        "HG.CMX": "BaseMetals",
        "ALI.CMX": "BaseMetals",
        "CL.NYM": "Energy",
        "NG.NYM": "Energy",
        "TA.CZC": "Petrochemicals",
        "J.DCE": "CoalAndSteel",
        "SA.CZC": "Chemicals",
        "S.CBT": "Grains",
        "C.CBT": "Grains",
        "W.CBT": "Grains",
        "ZE.CBT": "Grains",
        "LH.DCE": "Livestock",
        "RB.SHF": "Steel",
    }

    def __init__(self):
        """Initialize Wind provider with connection management."""
        self._w = None
        self._connected = False
        self._mock = MockProvider()
        self._initialize_wind()

    def _initialize_wind(self) -> None:
        """Initialize Wind API connection."""
        try:
            from WindPy import w
            self._w = w
            # Start Wind API connection
            logger.info("Starting Wind API connection...")
            result = self._w.start()
            if result.ErrorCode == 0:
                self._connected = True
                logger.info("Wind API connection established successfully")
            else:
                logger.error(f"Failed to connect to Wind API: ErrorCode={result.ErrorCode}, Data={result.Data}")
                self._connected = False
        except ImportError:
            logger.warning("WindPy not available - install WindPy via Wind terminal")
            self._w = None
            self._connected = False
        except Exception as e:
            logger.warning(f"Wind API not available: {e}")
            self._w = None
            self._connected = False

    def _ensure_connection(self) -> bool:
        """Ensure Wind API is connected."""
        if not self._connected or not self._w:
            logger.warning("Wind API not connected, attempting reconnection...")
            self._initialize_wind()
        return self._connected

    async def fetch_indices(self) -> Mapping[str, Any]:
        """Fetch global + A-share indices with unified schema."""
        if not self._ensure_connection():
            logger.warning("Wind API not available - returning demo indices")
            return self._get_demo_indices_data()

        fields = ["rt_last", "rt_chg", "rt_pct_chg", "rt_open", "rt_high", "rt_low", "rt_pre_close"]
        result = await self._wsq(self.INDEX_CODES, fields)
        if result is None or self._is_all_zero(result):
            # Fallback to static snapshot
            wss_fields = ["close", "pct_chg", "chg", "open", "high", "low", "pre_close"]
            result = await self._wss(self.INDEX_CODES, wss_fields)
            fields = wss_fields
        if result is None:
            return self._get_demo_indices_data()

        return self._map_price_result(self.INDEX_CODES, fields, result, include_volume=False)

    async def fetch_fx(self) -> Mapping[str, Any]:
        """Fetch FX data relevant to Chinese markets."""
        if not self._ensure_connection():
            return self._get_demo_fx_data()
            return self._get_demo_fx_data()

        fields = ["rt_last", "rt_chg", "rt_pct_chg"]
        result = await self._wsq(self.FX_CODES, fields)
        if result is None or self._is_all_zero(result):
            wss_fields = ["close", "chg", "pct_chg"]
            result = await self._wss(self.FX_CODES, wss_fields)
            fields = wss_fields
        if result is None:
            return self._get_demo_fx_data()

        return self._map_price_result(self.FX_CODES, fields, result, include_volume=False, decimals=4)

    async def fetch_rates(self) -> Mapping[str, Any]:
        """Fetch policy rates + CN/US govy yields."""
        if not self._ensure_connection():
            return self._get_demo_rates_data()

        rate_codes = self.POLICY_RATE_CODES + self.GOVY_CN_CODES + self.GOVY_US_CODES
        fields = ["rt_last", "rt_chg"]
        result = await self._wsq(rate_codes, fields)
        if result is None or self._is_all_zero(result):
            wss_fields = ["close", "chg"]
            result = await self._wss(rate_codes, wss_fields)
            fields = wss_fields
        if result is None:
            return self._get_demo_rates_data()

        return self._map_price_result(rate_codes, fields, result, include_volume=False, decimals=3)

    async def fetch_commodities(self) -> Mapping[str, Any]:
        """Fetch commodities futures snapshot (国内+海外)."""
        if not self._ensure_connection():
            return self._get_demo_commodities_data()

        fields = ["rt_last", "rt_chg", "rt_pct_chg", "rt_vol"]
        result = await self._wsq(self.COMMODITY_CODES, fields)
        if result is None or self._is_all_zero(result):
            wss_fields = ["close", "chg", "pct_chg", "pre_close", "volume"]
            result = await self._wss(self.COMMODITY_CODES, wss_fields)
            fields = wss_fields
        if result is None:
            return self._get_demo_commodities_data()

        data = self._map_price_result(self.COMMODITY_CODES, fields, result, include_volume=True, decimals=2)
        # add sector if known
        for code, item in data.items():
            if code in self.COMMODITY_SECTOR:
                item["sector"] = self.COMMODITY_SECTOR[code]
        return data

    async def fetch_us_stocks(self) -> Mapping[str, Any]:
        """Fetch US stock market data from Wind API."""
        if not self._ensure_connection():
            return self._get_demo_us_stocks_data()

        try:
            # US market indices and major stocks (verified codes)
            us_codes = [
                "DJI.GI",        # 道琼斯工业平均指数 (verified)
                "SPX.GI",        # 标普500指数 (verified)
                "IXIC.GI",       # 纳斯达克指数 (verified)
                "AAPL.O",        # 苹果 (verified)
                "MSFT.O",        # 微软 (verified)
                "GOOGL.O",       # 谷歌 (verified)
                "TSLA.O",        # 特斯拉 (verified) - Note: Wind might use TSL.O
                "AMZN.O",        # 亚马逊 (verified)
            ]

            # Use consistent field format
            fields = "rt_last,rt_chg,rt_pct_chg,rt_vol"

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._w.wsq(",".join(us_codes), fields)
            )

            if result.ErrorCode != 0:
                logger.warning(f"US stocks real-time data failed (ErrorCode: {result.ErrorCode}), trying simplified fields...")
                # Try with simplified fields if full fields fail
                result = await loop.run_in_executor(
                    None,
                    lambda: self._w.wsq(",".join(us_codes), "rt_last,rt_chg,rt_pct_chg")
                )

            if result.ErrorCode != 0:
                logger.error(f"US stocks data fetch failed: {result.ErrorCode}")
                return self._get_demo_us_stocks_data()

            us_stocks_data = {}
            current_time = datetime.now().isoformat()

            for i, code in enumerate(us_codes):
                if i < len(result.Data[0]) and result.Data[0][i] is not None:
                    last_price = result.Data[0][i] if result.Data[0][i] is not None else 0

                    us_stocks_data[code] = {
                        "code": code,
                        "name": self._get_us_stock_name(code),
                        "last": round(last_price, 2) if last_price > 0 else 0,
                        "timestamp": current_time,
                    }

                    # Add additional fields if available
                    if len(result.Data) > 1 and result.Data[1][i] is not None:
                        us_stocks_data[code]["change"] = round(result.Data[1][i], 2)

                    if len(result.Data) > 2 and result.Data[2][i] is not None:
                        us_stocks_data[code]["change_pct"] = round(result.Data[2][i], 2)

                    # Add volume if available
                    if len(result.Data) > 3 and result.Data[3][i] is not None:
                        us_stocks_data[code]["volume"] = result.Data[3][i]

            logger.info(f"Successfully fetched {len(us_stocks_data)} US stocks from Wind API")
            return us_stocks_data

        except Exception as e:
            logger.error(f"Error fetching US stocks data: {e}")
            return self._get_demo_us_stocks_data()

    async def fetch_crypto(self) -> Mapping[str, Any]:
        """Wind 暂缺稳定加密资产行情，返回示例数据。"""
        return self._get_demo_crypto_data()

    async def fetch_calendar(self) -> list[Mapping[str, Any]]:
        """Fetch economic calendar data."""
        if not self._ensure_connection():
            return []

        try:
            # Get upcoming economic events
            loop = asyncio.get_event_loop()
            today = datetime.now().strftime("%Y-%m-%d")

            # Wind economic calendar function
            result = await loop.run_in_executor(
                None,
                lambda: self._w.wsd("M0000001.SH", "CLOSE", today, today)
            )

            # Simplified calendar data - Wind's calendar API is complex
            # In production, you'd use Wind's specific calendar functions
            calendar_data = []

            return calendar_data

        except Exception as e:
            logger.error(f"Error fetching calendar data: {e}")
            return []

    async def fetch_a_share_short_term(self) -> Mapping[str, Any]:
        """Placeholder until dedicated Wind board/flow feeds are wired."""
        return await self._mock.fetch_a_share_short_term()

    def _get_demo_indices_data(self) -> Mapping[str, Any]:
        """Return demo indices data when Wind API is not available."""
        import random

        indices = {
            "000001.SH": {"name": "上证综指", "base": 3150},
            "399001.SZ": {"name": "深证成指", "base": 11200},
            "399006.SZ": {"name": "创业板指", "base": 2350},
            "000300.SH": {"name": "沪深300", "base": 4180},
            "000905.SH": {"name": "中证500", "base": 6850},
            "000852.SH": {"name": "中证1000", "base": 7200},
            "000016.SH": {"name": "上证50", "base": 2850},
            "399005.SZ": {"name": "中小板指", "base": 8500},
            "000688.SH": {"name": "科创50", "base": 1050},
        }

        demo_data = {}
        current_time = datetime.now().isoformat()

        for code, info in indices.items():
            change = random.uniform(-50, 50)
            change_pct = change / info["base"] * 100

            demo_data[code] = {
                "code": code,
                "name": info["name"],
                "display_name": info["name"],
                "last": round(info["base"] + change, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": round(random.uniform(100, 500), 2),  # 亿手
                "amount": round(random.uniform(1000, 5000), 2),  # 亿元
                "open": round(info["base"] + random.uniform(-30, 30), 2),
                "high": round(info["base"] + random.uniform(0, 60), 2),
                "low": round(info["base"] + random.uniform(-60, 0), 2),
                "prev_close": info["base"],
                "timestamp": current_time,
                "update_time": current_time,
            }

        return demo_data

    def _get_demo_fx_data(self) -> Mapping[str, Any]:
        """Return demo FX data when Wind API is not available."""
        import random

        fx_pairs = {
            "USDCNY.EX": 7.25,
            "EURCNY.EX": 7.85,
            "HKDCNY.EX": 0.92,
            "JPYCNY.EX": 0.048,
        }

        demo_data = {}
        for code, base in fx_pairs.items():
            change = random.uniform(-0.05, 0.05)
            change_pct = change / base * 100

            demo_data[code] = {
                "code": code,
                "last": round(base + change, 4),
                "change": round(change, 4),
                "change_pct": round(change_pct, 2),
                "timestamp": datetime.now().isoformat(),
            }

        return demo_data

    def _get_demo_rates_data(self) -> Mapping[str, Any]:
        """Return demo rates data when Wind API is not available."""
        import random

        rates = {
            "M0000017.SH": 2.85,  # 中10Y
            "M0000025.SH": 2.65,  # 中5Y
            "M0000007.SH": 2.45,  # 中3Y
            "M0000001.SH": 2.25,  # 中1Y
            "UST10Y.GBM": 3.95,   # 美10Y
            "UST2Y.GBM": 4.30,    # 美2Y
            "LPR1Y.IR": 3.45,
            "LPR5Y.IR": 3.95,
        }

        demo_data = {}
        for code, base in rates.items():
            change = random.uniform(-0.05, 0.05)

            demo_data[code] = {
                "code": code,
                "last": round(base + change, 3),
                "change": round(change, 3),
                "timestamp": datetime.now().isoformat(),
            }

        return demo_data

    async def _wsq(self, codes: list[str], fields: list[str]):
        """Run wsq in executor and return result or None on error."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._w.wsq(",".join(codes), ",".join(fields))
            )
            if result.ErrorCode != 0:
                logger.error(f"Wind WSQ failed: {result.ErrorCode}")
                return None
            return result
        except Exception as e:
            logger.error(f"Wind WSQ call failed: {e}")
            return None

    async def _wss(self, codes: list[str], fields: list[str]):
        """Run wss snapshot in executor and return result or None on error."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._w.wss(",".join(codes), ",".join(fields))
            )
            if result.ErrorCode != 0:
                logger.error(f"Wind WSS failed: {result.ErrorCode}")
                return None
            return result
        except Exception as e:
            logger.error(f"Wind WSS call failed: {e}")
            return None

    def _map_price_result(
        self,
        codes: list[str],
        fields: list[str],
        result: Any,
        include_volume: bool = False,
        decimals: int = 2,
    ) -> Mapping[str, Any]:
        """Map WSQ result to unified schema with common fields."""
        alias = {
            "rt_last": "last",
            "rt_chg": "change",
            "rt_pct_chg": "change_pct",
            "rt_open": "open",
            "rt_high": "high",
            "rt_low": "low",
            "rt_pre_close": "prev_close",
            "rt_vol": "volume",
            "rt_amt": "amount",
            "close": "last",
            "chg": "change",
            "pct_chg": "change_pct",
            "open": "open",
            "high": "high",
            "low": "low",
            "pre_close": "prev_close",
            "volume": "volume",
            "amt": "amount",
        }
        mapped = {}
        now = datetime.now().isoformat()
        # result.Data is list per field in order of fields
        for idx, code in enumerate(codes):
            item: dict[str, Any] = {"code": code, "timestamp": now}
            for f_index, field in enumerate(fields):
                if f_index >= len(result.Data):
                    continue
                values = result.Data[f_index]
                if idx >= len(values):
                    continue
                val = values[idx]
                try:
                    if val is None or (isinstance(val, float) and math.isnan(val)):
                        continue
                except Exception:
                    continue
                key = alias.get(field, field)
                if key in {"last", "change", "open", "high", "low", "prev_close"}:
                    item[key] = round(val, decimals)
                elif key == "change_pct":
                    item[key] = round(val, 2)
                elif key == "volume" and include_volume:
                    item[key] = val
                elif key == "amount" and include_volume:
                    item[key] = val
            item["name"] = self.NAME_MAP.get(code, code)
            # Derive change if missing but we have last/prev_close
            if "change" not in item and "last" in item and "prev_close" in item and item.get("prev_close"):
                delta = item["last"] - item["prev_close"]
                item["change"] = round(delta, decimals)
                if "change_pct" not in item and item["prev_close"]:
                    item["change_pct"] = round(delta / item["prev_close"] * 100, 2)
            mapped[code] = item
        return mapped

    @staticmethod
    def _is_all_zero(result: Any) -> bool:
        """Detect if result Data is all zeros (common when permission/closed)."""
        try:
            return all(
                all((v or 0) == 0 for v in series)
                for series in result.Data
            )
        except Exception:
            return False

    def _get_demo_commodities_data(self) -> Mapping[str, Any]:
        """Return demo commodities data when Wind API is not available."""
        import random

        commodities = {
            "RB00.SHF": 3800,     # 螺纹钢
            "I00.DCE": 850,       # 铁矿石
            "CU00.SHF": 68500,    # 沪铜
            "AL00.SHF": 18500,    # 沪铝
            "ZN00.SHF": 25200,    # 沪锌
            "AU00.SHF": 465,      # 沪金
            "AG00.SHF": 5650,     # 沪银
        }

        demo_data = {}
        for code, base in commodities.items():
            change = random.uniform(-base*0.03, base*0.03)
            change_pct = change / base * 100

            demo_data[code] = {
                "code": code,
                "last": round(base + change, 0),
                "change": round(change, 0),
                "change_pct": round(change_pct, 2),
                "volume": random.randint(10000, 100000),
                "timestamp": datetime.now().isoformat(),
            }

        return demo_data

    def _get_us_stock_name(self, code: str) -> str:
        """Get friendly name for US stock code."""
        names = {
            "DJI.GI": "道琼斯指数",
            "SPX.GI": "标普500",
            "IXIC.GI": "纳斯达克",
            "AAPL.O": "苹果",
            "MSFT.O": "微软",
            "GOOGL.O": "谷歌",
            "TSLA.O": "特斯拉",
            "AMZN.O": "亚马逊",
        }
        return names.get(code, code)

    def _get_demo_us_stocks_data(self) -> Mapping[str, Any]:
        """Return demo US stocks data when Wind API is not available."""
        import random

        us_stocks = {
            "DJI.GI": {"name": "道琼斯指数", "base": 35000},
            "SPX.GI": {"name": "标普500", "base": 4500},
            "IXIC.GI": {"name": "纳斯达克", "base": 15000},
            "AAPL.O": {"name": "苹果", "base": 180},
            "MSFT.O": {"name": "微软", "base": 330},
            "GOOGL.O": {"name": "谷歌", "base": 2800},
            "TSLA.O": {"name": "特斯拉", "base": 250},
            "AMZN.O": {"name": "亚马逊", "base": 150},
        }

        demo_data = {}
        current_time = datetime.now().isoformat()

        for code, info in us_stocks.items():
            change_pct = random.uniform(-3, 3)  # US stocks normal volatility
            change = info["base"] * change_pct / 100

            demo_data[code] = {
                "code": code,
                "name": info["name"],
                "last": round(info["base"] + change, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": random.randint(1000000, 50000000),
                "timestamp": current_time,
            }

        return demo_data

    def _get_demo_crypto_data(self) -> Mapping[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        return {
            "BTC.CC": {"code": "BTC.CC", "name": "比特币", "last": 63000, "change_pct": 1.2, "timestamp": timestamp},
            "ETH.CC": {"code": "ETH.CC", "name": "以太坊", "last": 3100, "change_pct": -0.8, "timestamp": timestamp},
            "SOL.CC": {"code": "SOL.CC", "name": "Solana", "last": 150, "change_pct": 3.2, "timestamp": timestamp},
        }

    def __del__(self):
        """Clean up Wind API connection on destruction."""
        try:
            if self._w and self._connected:
                self._w.stop()
                logger.info("Wind API connection closed")
        except Exception as e:
            logger.error(f"Error closing Wind API connection: {e}")


# Factory function for Wind provider
def create_wind_provider() -> WindProvider:
    """Create and return Wind provider instance."""
    return WindProvider()
