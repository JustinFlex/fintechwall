"""Open data provider backed by free APIs (Tencent + ExchangeRate + FRED + AlphaVantage)."""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from io import StringIO
from typing import Any, Mapping, Sequence
from urllib.parse import quote

import httpx

from app.core.settings import settings

from .base import MarketDataProvider
from .mock import MockProvider

logger = logging.getLogger(__name__)


class OpenProvider(MarketDataProvider):
    """Aggregate public data endpoints into the unified snapshot schema."""

    STOOQ_ENDPOINT = "https://stooq.com/q/l/"
    STOOQ_FIELDS = "sd2t2ohlcv"
    STOOQ_CACHE_TTL = 15.0
    FX_ENDPOINT = "https://open.er-api.com/v6/latest"
    CALENDAR_ENDPOINT = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    CALENDAR_CACHE_TTL = 1200.0
    FOREXFACTORY_COOLDOWN_TTL = 900.0
    CALENDAR_LOOKAHEAD_DAYS = 10
    TRADING_ECONOMICS_ENDPOINT = "https://api.tradingeconomics.com/calendar"
    TRADING_ECONOMICS_CREDENTIALS = "guest:guest"
    TRADING_ECONOMICS_LOOKAHEAD_DAYS = 7
    FRED_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    FRED_LOOKBACK_DAYS = 40
    FRED_CACHE_TTL = 300.0
    COINGECKO_ENDPOINT = "https://api.coingecko.com/api/v3/simple/price"
    COINGECKO_IDS = {
        "bitcoin": ("BTC.CC", "比特币"),
        "ethereum": ("ETH.CC", "以太坊"),
        "solana": ("SOL.CC", "Solana"),
        "binancecoin": ("BNB.CC", "BNB"),
        "ripple": ("XRP.CC", "XRP"),
    }
    CRYPTO_CACHE_TTL = 60.0
    GOLDPRICE_ENDPOINT = "https://data-asg.goldprice.org/dbXRates/USD"
    GOLDPRICE_CACHE_TTL = 60.0
    EASTMONEY_BOARD_ENDPOINT = "https://push2.eastmoney.com/api/qt/clist/get"
    EASTMONEY_BOARD_FIELDS = "f12,f14,f3,f62,f184,f204,f205"
    EASTMONEY_BOARD_LIMIT = 60
    EASTMONEY_HEADERS = {"Referer": "https://quote.eastmoney.com", "User-Agent": "Mozilla/5.0"}
    TENCENT_QUOTE_ENDPOINT = "http://qt.gtimg.cn/q="
    TENCENT_HEADERS = {"User-Agent": "Mozilla/5.0"}
    TENCENT_CACHE_TTL = 5.0
    ALPHAVANTAGE_ENDPOINT = "https://www.alphavantage.co/query"
    ALPHAVANTAGE_CACHE_TTL = 3600.0
    ALPHAVANTAGE_COMMODITY_SERIES = {
        "WTI": ("WTI", "CL.NYM", "WTI 原油"),
        "BRENT": ("BRENT", "COIL.BR", "布伦特原油"),
        "COPPER": ("COPPER", "HG.CMX", "COMEX 铜"),
        "NATURAL_GAS": ("NATURAL_GAS", "NG.NYM", "NYMEX 天然气"),
    }
    YAHOO_COMMODITY_SYMBOLS = {
        "CL=F": ("CL.NYM", "WTI 原油", 2),
        "BZ=F": ("COIL.BR", "布伦特原油", 2),
        "NG=F": ("NG.NYM", "NYMEX 天然气", 3),
        "HG=F": ("HG.CMX", "COMEX 铜", 2),
        "GC=F": ("GC.CMX", "COMEX 黄金", 2),
        "SI=F": ("SI.CMX", "COMEX 白银", 2),
        "PL=F": ("PL.NYM", "NYMEX 铂金", 2),
        "PA=F": ("PA.NYM", "NYMEX 钯金", 2),
        "ZC=F": ("ZC.CBT", "CBOT 玉米", 2),
        "ZS=F": ("ZS.CBT", "CBOT 大豆", 2),
        "KC=F": ("KC.NYB", "ICE 咖啡", 2),
    }
    YAHOO_RATE_SYMBOLS = {
        "^TNX": ("UST10Y.GBM", "美债10Y", 4),
        "^FVX": ("UST5Y.GBM", "美债5Y", 4),
        "^IRX": ("UST3M.GBM", "美债3M", 4),
    }
    CHINABOND_YIELD_URL = "http://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo"
    CHINABOND_CACHE_TTL = 600.0
    CHINABOND_PARAMS = {"locale": "en_US", "nameType": 1}
    FXSTREET_CALENDAR_URL = "https://www.fxstreet.com/economic-calendar"
    FXSTREET_CACHE_TTL = 300.0
    FXSTREET_MAX_EVENTS = 15
    NASDAQ_CALENDAR_ENDPOINT = "https://api.nasdaq.com/api/calendar/economicevents"
    NASDAQ_HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    NASDAQ_LOOKAHEAD_DAYS = 7
    CHINA_GOVERNMENT_CODES = {
        1: ("M0000001.SH", "中国国债1Y"),
        3: ("M0000007.SH", "中国国债3Y"),
        5: ("M0000025.SH", "中国国债5Y"),
        10: ("M0000017.SH", "中国国债10Y"),
        15: ("M0000021.SH", "中国国债15Y"),
    }
    FRED_COMMODITY_SERIES = {
        "DCOILWTICO": ("CL.NYM", "WTI 原油", 2),
        "DCOILBRENTEU": ("COIL.BR", "布伦特原油", 2),
        "DHHNGSP": ("NG.NYM", "亨利港天然气", 2),
        "PCOPPUSDM": ("HG.CMX", "LME 铜(USD/MT)", 2),
    }
    TENCENT_A_INDEX_CODES = {
        "sh000001": ("000001.SH", "上证综指"),
        "sz399001": ("399001.SZ", "深证成指"),
        "sz399006": ("399006.SZ", "创业板指"),
        "sh000300": ("000300.SH", "沪深300"),
        "sh000905": ("000905.SH", "中证500"),
        "sh000852": ("000852.SH", "中证1000"),
        "sh000016": ("000016.SH", "上证50"),
    }
    TENCENT_GLOBAL_INDICES = {
        "hkHSI": ("HSI.HI", "恒生指数"),
        "hkHSCEI": ("HSCEI.HI", "恒生中国企业"),
        "usDJI": ("DJI.GI", "道琼斯"),
        "usINX": ("SPX.GI", "标普500"),
        "usIXIC": ("IXIC.GI", "纳斯达克"),
        "usNDX": ("NDXTMC.GI", "纳指100"),
    }
    TENCENT_US_STOCKS = {
        "usAAPL": ("AAPL.O", "苹果"),
        "usMSFT": ("MSFT.O", "微软"),
        "usGOOGL": ("GOOGL.O", "谷歌"),
        "usTSLA": ("TSLA.O", "特斯拉"),
        "usAMZN": ("AMZN.O", "亚马逊"),
        "usMETA": ("META.O", "Meta"),
        "usNVDA": ("NVDA.O", "英伟达"),
    }
    TENCENT_COMMODITIES = {
        "hf_CL": ("CL.NYM", "WTI 原油"),
        "hf_GC": ("GC.CMX", "COMEX 黄金"),
        "hf_SI": ("SI.CMX", "COMEX 白银"),
        "hf_HG": ("HG.CMX", "COMEX 铜"),
        "hf_NG": ("NG.NYM", "NYMEX 天然气"),
    }
    REQUEST_TIMEOUT = 10.0
    MAX_RETRIES = 2

    STOOQ_INDICES = {
        "^SPX": ("SPX.GI", "标普500"),
        "^DJI": ("DJI.GI", "道琼斯"),
        "^IXIC": ("IXIC.GI", "纳斯达克"),
        "^HSI": ("HSI.HI", "恒生指数"),
        "^N225": ("N225.GI", "日经225"),
        "000001.SS": ("000001.SH", "上证综指"),
        "399001.SZ": ("399001.SZ", "深证成指"),
        "399006.SZ": ("399006.SZ", "创业板指"),
        "000300.SS": ("000300.SH", "沪深300"),
        "000852.SS": ("000852.SH", "中证1000"),
        "000016.SS": ("000016.SH", "上证50"),
        "000905.SS": ("000905.SH", "中证500"),
        "^STOXX50E": ("SX5E.GI", "欧元区50"),
        "^FTSE": ("UKX.GI", "富时100"),
        "^FCHI": ("CAC.GI", "法国CAC40"),
        "^GDAXI": ("DAX.GI", "德国DAX"),
    }

    STOOQ_US_STOCKS = {
        "AAPL.US": ("AAPL.O", "苹果"),
        "MSFT.US": ("MSFT.O", "微软"),
        "GOOGL.US": ("GOOGL.O", "谷歌"),
        "TSLA.US": ("TSLA.O", "特斯拉"),
        "AMZN.US": ("AMZN.O", "亚马逊"),
        "^SPX": ("SPX.GI", "标普500"),
        "^DJI": ("DJI.GI", "道琼斯"),
        "^IXIC": ("IXIC.GI", "纳斯达克"),
    }

    STOOQ_COMMODITIES = {
        "CL.F": ("CL.NYM", "NYMEX WTI 原油"),
        "GC.F": ("GC.CMX", "COMEX 黄金"),
        "SI.F": ("SI.CMX", "COMEX 白银"),
        "HG.F": ("HG.CMX", "COMEX 铜"),
        "NG.F": ("NG.NYM", "NYMEX 天然气"),
        "RB.F": ("RB.SHF", "螺纹钢(合约近月)"),
    }

    FX_PAIRS = {
        ("USD", "CNY"): ("USDCNY.EX", "USD/CNY"),
        ("USD", "CNH"): ("USDCNH.FX", "USD/CNH"),
        ("EUR", "USD"): ("EURUSD.FX", "EUR/USD"),
        ("USD", "JPY"): ("USDJPY.FX", "USD/JPY"),
        ("USD", "HKD"): ("USDHKD.FX", "USD/HKD"),
        ("GBP", "USD"): ("GBPUSD.FX", "GBP/USD"),
    }

    FRED_RATE_SERIES = {
        "DGS10": ("UST10Y.GBM", "美债10Y"),
        "DGS2": ("UST2Y.GBM", "美债2Y"),
        "SOFR": ("SOFR.IR", "SOFR隔夜融资"),
        "IUDSOIA": ("SONIA.IR", "SONIA(英镑)"),
        "EFFR": ("EFFR.IR", "联邦基金有效利率"),
    }

    def __init__(self) -> None:
        self._mock = MockProvider()
        self._stooq_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._fred_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._calendar_cache: tuple[float, list[Mapping[str, Any]]] | None = None
        self._forexfactory_backoff_until: float = 0.0
        self._crypto_cache: tuple[float, dict[str, Any]] | None = None
        self._tencent_cache: dict[str, tuple[float, str]] = {}
        self._alphavantage_cache: dict[str, tuple[float, list[Mapping[str, Any]]]] = {}
        self._chinabond_cache: tuple[float, dict[str, Any]] | None = None
        self._fxstreet_cache: tuple[float, list[Mapping[str, Any]]] | None = None
        self._goldprice_cache: tuple[float, dict[str, Any]] | None = None

    async def fetch_indices(self) -> Mapping[str, Any]:
        fallback = await self._mock.fetch_indices()
        payload = dict(fallback)
        cn_indices = await self._fetch_tencent_indices(self.TENCENT_A_INDEX_CODES)
        payload.update(cn_indices)
        global_indices = await self._fetch_tencent_indices(self.TENCENT_GLOBAL_INDICES)
        payload.update(global_indices)

        stooq_targets = {
            symbol: mapping
            for symbol, mapping in self.STOOQ_INDICES.items()
            if mapping[0] not in payload
        }
        quotes = await self._fetch_stooq_quotes(stooq_targets)
        for symbol, raw in quotes.items():
            code, label = stooq_targets[symbol]
            payload[code] = self._quote_to_snapshot(raw, code, label)
        return payload

    async def fetch_fx(self) -> Mapping[str, Any]:
        rates = await self._fetch_fx_rates()
        if not rates:
            return await self._mock.fetch_fx()

        fx_payload: dict[str, Any] = {}
        timestamp = datetime.utcnow().isoformat()

        for (base, quote), (code, label) in self.FX_PAIRS.items():
            price = self._resolve_cross(rates, base, quote)
            if price is None:
                continue
            fx_payload[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(price, 6 if price < 1 else 4),
                "change": 0.0,
                "change_pct": 0.0,
                "timestamp": timestamp,
            }

        return fx_payload or await self._mock.fetch_fx()

    async def fetch_rates(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {}
        yahoo_payload = await self._fetch_yahoo_rates()
        payload.update(yahoo_payload)
        cgb_payload = await self._fetch_cngb_yields()
        payload = self._merge_by_recency(payload, cgb_payload)
        fred_payload = await self._fetch_fred_rates()
        payload = self._merge_by_recency(payload, fred_payload)
        lpr_payload = await self._fetch_lpr_rates()
        payload = self._merge_by_recency(payload, lpr_payload)
        if payload:
            return payload
        return await self._mock.fetch_rates()

    async def fetch_commodities(self) -> Mapping[str, Any]:
        # 全量依赖 Yahoo 期货报价，确保口径一致；若完全缺失则回退到 Mock
        payload = await self._fetch_yahoo_commodities()
        if payload:
            return payload

        return await self._mock.fetch_commodities()

    async def fetch_us_stocks(self) -> Mapping[str, Any]:
        fallback = await self._mock.fetch_us_stocks()
        payload = dict(fallback)
        us_payload = await self._fetch_tencent_indices(self.TENCENT_US_STOCKS)
        payload.update(us_payload)

        missing = {
            symbol: mapping
            for symbol, mapping in self.STOOQ_US_STOCKS.items()
            if mapping[0] not in payload
        }
        if missing:
            quotes = await self._fetch_stooq_quotes(missing)
            for symbol, raw in quotes.items():
                code, label = missing[symbol]
                payload[code] = self._quote_to_snapshot(raw, code, label)
        return payload

    async def fetch_calendar(self) -> list[Mapping[str, Any]]:
        events = await self._fetch_calendar_feed()
        events = self._filter_future_events(events)
        if events:
            return events
        fallback = await self._mock.fetch_calendar()
        return self._filter_future_events(fallback) or fallback

    async def fetch_crypto(self) -> Mapping[str, Any]:
        fallback = await self._mock.fetch_crypto()
        payload = await self._fetch_crypto_prices()
        if not payload:
            return fallback

        snapshot: dict[str, Any] = {}
        timestamp = datetime.utcnow().isoformat()
        for asset_id, raw in payload.items():
            mapping = self.COINGECKO_IDS.get(asset_id)
            if not mapping:
                continue
            code, label = mapping
            last = raw.get("usd")
            if last is None:
                continue
            last_value = float(last)
            change_pct = float(raw.get("usd_24h_change", 0.0) or 0.0)
            denom = 1 + (change_pct / 100)
            prev_close = last_value / denom if denom else last_value
            snapshot[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(last_value, 2),
                "change_pct": round(float(change_pct), 2),
                "change": round(last_value - float(prev_close), 2),
                "prev_close": round(float(prev_close), 2),
                "timestamp": timestamp,
            }
        return snapshot or fallback

    async def fetch_a_share_short_term(self) -> Mapping[str, Any]:
        fallback = await self._mock.fetch_a_share_short_term()
        boards = await self._fetch_board_rankings()
        if not boards:
            return fallback

        def pct_value(entry: Mapping[str, Any]) -> float:
            value = entry.get("change_pct")
            return float(value) if isinstance(value, (int, float)) else 0.0

        def flow_value(entry: Mapping[str, Any]) -> float:
            value = entry.get("net_flow")
            return float(value) if isinstance(value, (int, float)) else 0.0

        hot = sorted(boards, key=pct_value, reverse=True)[:6]
        cold = sorted(boards, key=pct_value)[:6]
        capital_pool = [entry for entry in boards if entry.get("net_flow") is not None]
        capital_pool.sort(key=flow_value, reverse=True)
        capital = capital_pool[:6] if capital_pool else hot[:6]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "eastmoney",
            "hot_boards": hot,
            "cold_boards": cold,
            "capital_boards": capital,
        }

    async def _fetch_crypto_prices(self) -> dict[str, Any]:
        now = time.time()
        if self._crypto_cache and now - self._crypto_cache[0] < self.CRYPTO_CACHE_TTL:
            return self._crypto_cache[1]

        ids = ",".join(self.COINGECKO_IDS.keys())
        url = (
            f"{self.COINGECKO_ENDPOINT}"
            f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        )
        payload = await self._http_get_json(url)
        if isinstance(payload, dict):
            self._crypto_cache = (now, payload)
            return payload
        return {}

    async def _fetch_board_rankings(self) -> list[dict[str, Any]]:
        params = {
            "pn": 1,
            "pz": self.EASTMONEY_BOARD_LIMIT,
            "po": 1,
            "np": 1,
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:90+t:2",
            "fields": self.EASTMONEY_BOARD_FIELDS,
        }
        payload = await self._http_get_json(
            self.EASTMONEY_BOARD_ENDPOINT,
            params=params,
            headers=self.EASTMONEY_HEADERS,
            trust_env=False,
        )
        if not isinstance(payload, dict):
            payload = await self._http_get_json(
                self._wrap_proxy(self.EASTMONEY_BOARD_ENDPOINT),
                params=params,
                headers=self.EASTMONEY_HEADERS,
                trust_env=False,
            )
        if not isinstance(payload, dict):
            return []
        data = payload.get("data") or {}
        diff = data.get("diff")
        if not isinstance(diff, list):
            return []
        boards: list[dict[str, Any]] = []
        for row in diff:
            if not isinstance(row, Mapping):
                continue
            entry = self._parse_board_row(row)
            if entry:
                boards.append(entry)
        return boards

    async def _fetch_tencent_indices(self, mapping: Mapping[str, tuple[str, str]]) -> dict[str, Any]:
        raw_entries = await self._fetch_tencent_data(mapping.keys())
        indices: dict[str, Any] = {}
        for symbol, (code, label) in mapping.items():
            raw = raw_entries.get(symbol)
            if not raw:
                continue
            tokens = raw.split("~")
            snapshot = self._tencent_tokens_to_snapshot(tokens, code, label)
            if snapshot:
                indices[code] = snapshot
        return indices

    async def _fetch_tencent_commodities(self) -> dict[str, Any]:
        raw_entries = await self._fetch_tencent_data(self.TENCENT_COMMODITIES.keys())
        payload: dict[str, Any] = {}
        for symbol, (code, label) in self.TENCENT_COMMODITIES.items():
            raw = raw_entries.get(symbol)
            if not raw:
                continue
            snapshot = self._parse_tencent_commodity_value(raw, code, label)
            if snapshot:
                payload[code] = snapshot
        return payload

    async def _fetch_tencent_data(self, symbols: Sequence[str]) -> dict[str, str]:
        if not symbols:
            return {}
        now = time.time()
        cached: dict[str, str] = {}
        pending: list[str] = []
        for symbol in symbols:
            entry = self._tencent_cache.get(symbol)
            if entry and now - entry[0] < self.TENCENT_CACHE_TTL:
                cached[symbol] = entry[1]
                continue
            pending.append(symbol)

        fetched: dict[str, str] = {}
        chunk_size = 15
        for i in range(0, len(pending), chunk_size):
            chunk = pending[i : i + chunk_size]
            query = ",".join(chunk)
            text = await self._http_get_text(
                f"{self.TENCENT_QUOTE_ENDPOINT}{query}",
                headers=self.TENCENT_HEADERS,
            )
            if not text:
                continue
            for symbol, value in self._parse_tencent_response(text).items():
                fetched[symbol] = value
                self._tencent_cache[symbol] = (now, value)

        return {**cached, **fetched}

    def _tencent_tokens_to_snapshot(
        self,
        tokens: Sequence[str],
        code: str,
        label: str,
        decimals: int = 2,
    ) -> dict[str, Any] | None:
        if len(tokens) < 5:
            return None
        last = self._safe_float(tokens[3])
        prev_close = self._safe_float(tokens[4])
        open_price = self._safe_float(tokens[5])
        if last is None or prev_close is None:
            return None
        change = self._safe_float(tokens[31]) if len(tokens) > 31 else None
        change_pct = self._safe_float(tokens[32]) if len(tokens) > 32 else None
        high = self._safe_float(tokens[33]) if len(tokens) > 33 else None
        low = self._safe_float(tokens[34]) if len(tokens) > 34 else None
        timestamp_raw = tokens[30] if len(tokens) > 30 else None
        timestamp = self._parse_tencent_timestamp(timestamp_raw)

        if change is None:
            change = last - prev_close
        if change_pct is None and prev_close:
            change_pct = (change / prev_close * 100) if prev_close else None

        snapshot = {
            "code": code,
            "name": label,
            "display_name": label,
            "last": round(last, decimals),
            "change": round(change or 0.0, decimals),
            "change_pct": round(change_pct or 0.0, 2),
            "open": round(open_price, decimals) if open_price is not None else None,
            "high": round(high, decimals) if high is not None else None,
            "low": round(low, decimals) if low is not None else None,
            "prev_close": round(prev_close, decimals),
            "timestamp": timestamp,
        }
        return snapshot

    def _parse_tencent_commodity_value(self, raw: str, code: str, label: str) -> dict[str, Any] | None:
        parts = raw.split(",")
        if len(parts) < 13:
            return None
        last = self._safe_float(parts[0])
        change = self._safe_float(parts[1])
        prev_close = self._safe_float(parts[2])
        open_price = self._safe_float(parts[3])
        high = self._safe_float(parts[4])
        low = self._safe_float(parts[5])
        time_part = parts[6]
        date_part = parts[12]
        timestamp = self._parse_tencent_datetime(date_part, time_part)
        if last is None or prev_close is None:
            return None
        change = change if change is not None else (last - prev_close)
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        snapshot = {
            "code": code,
            "name": label,
            "display_name": label,
            "last": round(last, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "open": round(open_price, 2) if open_price is not None else None,
            "high": round(high, 2) if high is not None else None,
            "low": round(low, 2) if low is not None else None,
            "prev_close": round(prev_close, 2),
            "timestamp": timestamp,
        }
        return snapshot

    def _parse_tencent_response(self, text: str) -> dict[str, str]:
        entries: dict[str, str] = {}
        for line in text.strip().split(";"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            prefix, rest = line.split("=", 1)
            symbol = prefix.split("v_")[-1]
            value = rest.strip().strip(";").strip("\"")
            if value:
                entries[symbol] = value
        return entries

    def _parse_tencent_timestamp(self, raw: str | None) -> str:
        if not raw:
            return datetime.utcnow().isoformat()
        raw = raw.strip()
        for fmt in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.isoformat()
            except Exception:
                continue
        return datetime.utcnow().isoformat()

    def _parse_tencent_datetime(self, date_part: str | None, time_part: str | None) -> str:
        if date_part and time_part:
            try:
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                return dt.isoformat()
            except Exception:
                pass
        return datetime.utcnow().isoformat()

    def _parse_board_row(self, row: Mapping[str, Any]) -> dict[str, Any] | None:
        code = row.get("f12")
        name = row.get("f14")
        if not code or not name:
            return None
        change_pct = self._safe_float(row.get("f3"))
        net_flow = self._safe_float(row.get("f62"))
        turnover = self._safe_float(row.get("f184") or row.get("f204") or row.get("f205"))
        entry: dict[str, Any] = {
            "code": code,
            "name": name,
            "display_name": name,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "net_flow": self._to_billion(net_flow),
            "turnover_rate": round(turnover, 2) if turnover is not None else None,
        }
        return entry

    def _to_billion(self, value: float | None) -> float | None:
        if value is None:
            return None
        try:
            return round(value / 10000, 2)
        except Exception:
            return None

    async def _fetch_goldprice_metals(self) -> dict[str, Any]:
        now = time.time()
        if self._goldprice_cache and now - self._goldprice_cache[0] < self.GOLDPRICE_CACHE_TTL:
            return dict(self._goldprice_cache[1])

        payload = await self._http_get_json(self.GOLDPRICE_ENDPOINT, headers={"User-Agent": "Mozilla/5.0"})
        if not isinstance(payload, Mapping):
            return {}
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return {}
        row = items[0]
        timestamp = self._parse_goldprice_timestamp(payload.get("date")) or datetime.utcnow().isoformat()
        entries: dict[str, Any] = {}
        xau_last = self._safe_float(row.get("xauPrice"))
        if xau_last is not None:
            change = self._safe_float(row.get("chgXau")) or 0.0
            pct = self._safe_float(row.get("pcXau")) or 0.0
            prev = xau_last - change
            entries["GC.CMX"] = {
                "code": "GC.CMX",
                "name": "COMEX 黄金",
                "display_name": "COMEX 黄金",
                "last": round(xau_last, 2),
                "change": round(change, 2),
                "change_pct": round(pct, 2),
                "prev_close": round(prev, 2),
                "timestamp": timestamp,
                "source": "goldprice.org",
            }
        xag_last = self._safe_float(row.get("xagPrice"))
        if xag_last is not None:
            change = self._safe_float(row.get("chgXag")) or 0.0
            pct = self._safe_float(row.get("pcXag")) or 0.0
            prev = xag_last - change
            entries["SI.CMX"] = {
                "code": "SI.CMX",
                "name": "COMEX 白银",
                "display_name": "COMEX 白银",
                "last": round(xag_last, 2),
                "change": round(change, 2),
                "change_pct": round(pct, 2),
                "prev_close": round(prev, 2),
                "timestamp": timestamp,
                "source": "goldprice.org",
            }

        if entries:
            self._goldprice_cache = (now, entries)
        return entries

    async def _fetch_yahoo_commodities(self) -> dict[str, Any]:
        return await self._fetch_yahoo_quotes(self.YAHOO_COMMODITY_SYMBOLS)

    async def _fetch_yahoo_rates(self) -> dict[str, Any]:
        return await self._fetch_yahoo_quotes(self.YAHOO_RATE_SYMBOLS)

    async def _fetch_yahoo_quotes(self, mapping: Mapping[str, tuple[str, str, int]]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for symbol, (code, label, decimals) in mapping.items():
            quote = await self._get_yahoo_chart(symbol)
            if not quote:
                continue
            last = quote.get("last")
            prev_close = quote.get("prev_close")
            if last is None or prev_close is None:
                continue
            change = last - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0
            payload[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(last, decimals),
                "change": round(change, decimals),
                "change_pct": round(change_pct, 2),
                "prev_close": round(prev_close, decimals),
                "open": round(quote["open"], decimals) if quote.get("open") is not None else None,
                "high": round(quote["high"], decimals) if quote.get("high") is not None else None,
                "low": round(quote["low"], decimals) if quote.get("low") is not None else None,
                "volume": quote.get("volume"),
                "timestamp": quote.get("timestamp") or datetime.utcnow().isoformat(),
                "source": "yahoo_chart",
            }
        return payload

    async def _get_yahoo_chart(self, symbol: str) -> dict[str, Any] | None:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}"
        params = {"range": "1d", "interval": "5m"}
        data = await self._http_get_json(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        if not isinstance(data, Mapping):
            return None
        result = (data.get("chart") or {}).get("result")
        if not result or not isinstance(result, list):
            return None
        meta = result[0].get("meta") or {}
        last = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
        open_price = meta.get("regularMarketOpen")
        high = meta.get("regularMarketDayHigh")
        low = meta.get("regularMarketDayLow")
        volume = meta.get("regularMarketVolume")
        ts_raw = meta.get("regularMarketTime")
        timestamp = datetime.utcfromtimestamp(ts_raw).isoformat() if ts_raw else datetime.utcnow().isoformat()
        return {
            "last": self._safe_float(last),
            "prev_close": self._safe_float(prev_close),
            "open": self._safe_float(open_price),
            "high": self._safe_float(high),
            "low": self._safe_float(low),
            "volume": volume if isinstance(volume, (int, float)) else None,
            "timestamp": timestamp,
        }

    async def _fetch_lpr_rates(self) -> dict[str, Any]:
        # LPR seldom changes intra-month; attempt public source, otherwise skip to avoid硬编码
        return {}

    async def _fetch_chinamoney_yields(self) -> dict[str, Any]:
        # Deprecated in favor of Eastmoney treasury feed; retained for compatibility
        return {}

    async def _fetch_cngb_yields(self) -> dict[str, Any]:
        now = time.time()
        if self._chinabond_cache and now - self._chinabond_cache[0] < self.CHINABOND_CACHE_TTL:
            return dict(self._chinabond_cache[1])

        text = await self._http_get_text(
            self._wrap_proxy(self.CHINABOND_YIELD_URL),
            params=self.CHINABOND_PARAMS,
            headers={"User-Agent": "Mozilla/5.0"},
            trust_env=False,
        )
        entries = self._parse_chinabond_table(text)
        if entries:
            self._chinabond_cache = (now, entries)
        return dict(entries)

    def _parse_chinabond_table(self, text: str | None) -> dict[str, Any]:
        if not text:
            return {}

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        tenor_map = {
            "1Y": self.CHINA_GOVERNMENT_CODES[1],
            "3Y": self.CHINA_GOVERNMENT_CODES[3],
            "5Y": self.CHINA_GOVERNMENT_CODES[5],
            "10Y": self.CHINA_GOVERNMENT_CODES[10],
        }
        current_date: str | None = None
        entries: dict[str, Any] = {}

        for raw_line in lines:
            date_match = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(.*)", raw_line)
            line = raw_line
            if date_match:
                current_date = date_match.group(1)
                line = date_match.group(2).strip()

            maturity_match = re.match(r"^(\d{1,3}\s*(?:Y|YR|MO))\s+(.*)", line, re.IGNORECASE)
            if not maturity_match:
                continue

            maturity_raw = maturity_match.group(1)
            numbers = re.findall(r"-?\d+\.\d+", maturity_match.group(2))
            if not numbers:
                continue

            last = self._safe_float(numbers[0])
            if last is None:
                continue

            change_bp = self._safe_float(numbers[1]) if len(numbers) > 1 else 0.0
            maturity_norm = maturity_raw.upper().replace(" ", "")
            maturity_norm = maturity_norm.replace("YR", "Y").replace("MO", "M")

            mapping = tenor_map.get(maturity_norm)
            if not mapping:
                continue
            code, label = mapping

            change_val = (change_bp or 0.0) / 100
            timestamp = (
                f"{current_date}T00:00:00" if current_date else datetime.utcnow().isoformat()
            )
            entries[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(last, 4),
                "change": round(change_val, 4),
                "prev_close": round(last - change_val, 4) if change_val is not None else None,
                "timestamp": timestamp,
                "source": "chinabond_mof",
            }

        return entries

    def _inject_lpr_rates(self, payload: dict[str, Any]) -> None:
        # LPR 暂无开放稳定源，如需展示请在 _fetch_lpr_rates 中填充真实抓取结果
        return

    async def _fetch_fx_rates(self) -> dict[str, float] | None:
        url = f"{self.FX_ENDPOINT}/USD"
        response_json = await self._http_get_json(url)
        if not response_json:
            return None
        if response_json.get("result") != "success":
            logger.warning("FX API returned error payload: %s", response_json)
            return None
        return response_json.get("rates") or None

    async def _fetch_stooq_quotes(self, mapping: Mapping[str, tuple[str, str]]) -> dict[str, dict[str, Any]]:
        if not mapping:
            return {}

        now = time.time()
        cached: dict[str, dict[str, Any]] = {}
        pending: list[str] = []
        for symbol in mapping:
            entry = self._stooq_cache.get(symbol)
            if entry and now - entry[0] < self.STOOQ_CACHE_TTL:
                data = entry[1]
                if data:
                    cached[symbol] = data
                continue
            pending.append(symbol)

        fetched: dict[str, dict[str, Any]] = {}
        if pending:
            batch = await self._fetch_stooq_batch(pending)
            for sym, data in batch.items():
                fetched[sym] = data
                self._stooq_cache[sym] = (now, data)
            missing = {sym for sym in pending if sym not in batch}
            for sym in missing:
                self._stooq_cache[sym] = (now, {})

        return {**cached, **fetched}

    async def _fetch_stooq_batch(self, symbols: Sequence[str]) -> dict[str, dict[str, Any]]:
        if not symbols:
            return {}
        encoded = [quote(symbol.lower(), safe="") for symbol in symbols]
        symbol_param = "+".join(encoded)
        url = (
            f"{self.STOOQ_ENDPOINT}?s={symbol_param}"
            f"&f={self.STOOQ_FIELDS}&e=csv&i=d"
        )
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                resp = await client.get(url)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Batch Stooq request failed: %s", exc)
            return {}

        text = resp.text.strip()
        if not text:
            return {}

        reader = csv.reader(StringIO(text))
        quotes: dict[str, dict[str, Any]] = {}
        for row in reader:
            if len(row) < 8:
                continue
            symbol = row[0].upper()
            if "N/D" in row[1:]:
                continue
            quotes[symbol] = {
                "symbol": symbol,
                "date": row[1],
                "time": row[2],
                "open": self._safe_float(row[3]),
                "high": self._safe_float(row[4]),
                "low": self._safe_float(row[5]),
                "close": self._safe_float(row[6]),
                "volume": self._safe_float(row[7]),
            }
        return quotes

    async def _http_get_json(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        trust_env: bool = True,
    ) -> dict[str, Any] | None:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.REQUEST_TIMEOUT,
                    headers=headers,
                    trust_env=trust_env,
                ) as client:
                    resp = await client.get(url, params=params)
                resp.raise_for_status()
                try:
                    return resp.json()
                except Exception:
                    parsed = self._extract_json_from_text(resp.text)
                    if parsed is not None:
                        return parsed
                    logger.warning(
                        "Failed to parse JSON from %s (attempt %s/%s)",
                        url,
                        attempt,
                        self.MAX_RETRIES,
                    )
            except Exception as exc:
                logger.warning(
                    "HTTP GET %s failed (attempt %s/%s): %s",
                    url,
                    attempt,
                    self.MAX_RETRIES,
                    exc,
                )
                await asyncio.sleep(0.3 * attempt)
        return None

    async def _http_get_text(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        encoding: str | None = None,
        trust_env: bool = True,
    ) -> str | None:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.REQUEST_TIMEOUT,
                    headers=headers,
                    max_redirects=2,
                    trust_env=trust_env,
                ) as client:
                    resp = await client.get(url, params=params)
                resp.raise_for_status()
                if encoding:
                    resp.encoding = encoding
                return resp.text
            except Exception as exc:
                logger.warning(
                    "HTTP GET %s failed (attempt %s/%s): %s",
                    url,
                    attempt,
                    self.MAX_RETRIES,
                    exc,
                )
                await asyncio.sleep(0.3 * attempt)
        return None

    def _quote_to_snapshot(
        self,
        raw: Mapping[str, Any],
        code: str,
        label: str,
        decimals: int = 2,
    ) -> Mapping[str, Any]:
        last = raw.get("close") or 0.0
        open_price = raw.get("open") or last
        high = raw.get("high")
        low = raw.get("low")
        volume = raw.get("volume")
        change = (last - open_price) if open_price else 0.0
        change_pct = (change / open_price * 100) if open_price else 0.0
        timestamp = self._derive_timestamp(raw)

        snapshot = {
            "code": code,
            "name": label,
            "display_name": label,
            "last": round(last, decimals),
            "change": round(change, decimals),
            "change_pct": round(change_pct, 2),
            "open": round(open_price, decimals),
            "high": round(high, decimals) if high is not None else None,
            "low": round(low, decimals) if low is not None else None,
            "prev_close": round(last - change, decimals),
            "timestamp": timestamp,
        }
        if volume is not None:
            snapshot["volume"] = volume
        return snapshot

    def _derive_timestamp(self, raw: Mapping[str, Any]) -> str:
        date_str = raw.get("date")
        time_str = raw.get("time") or "000000"
        if date_str and len(date_str) == 8:
            try:
                dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                return dt.isoformat()
            except Exception:
                pass
        return datetime.utcnow().isoformat()

    def _safe_float(self, value: Any) -> float | None:
        if value in (None, "", "N/D"):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _resolve_cross(self, rates: Mapping[str, float], base: str, quote: str) -> float | None:
        base = base.upper()
        quote = quote.upper()
        if base == quote:
            return 1.0
        try:
            if base == "USD":
                return rates.get(quote)
            if quote == "USD":
                base_rate = rates.get(base)
                return (1 / base_rate) if base_rate else None
            base_rate = rates.get(base)
            quote_rate = rates.get(quote)
            if not base_rate or not quote_rate:
                return None
            # rates dict expresses amount per USD, so convert via USD
            usd_per_base = 1 / base_rate
            return quote_rate * usd_per_base
        except Exception:
            return None

    async def _fetch_fred_rates(self) -> dict[str, Any]:
        tasks = {
            series_id: asyncio.create_task(self._get_fred_series(series_id))
            for series_id in self.FRED_RATE_SERIES
        }
        rates: dict[str, Any] = {}
        for series_id, task in tasks.items():
            data = await task
            if not data:
                continue
            code, label = self.FRED_RATE_SERIES[series_id]
            latest = data["value"]
            prev = data.get("previous")
            change = (latest - prev) if prev is not None else 0.0
            rates[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(latest, 4),
                "change": round(change, 4),
                "timestamp": data.get("date") or datetime.utcnow().isoformat(),
            }
        return rates

    async def _get_fred_series(self, series_id: str) -> dict[str, Any] | None:
        now = time.time()
        cached = self._fred_cache.get(series_id)
        if cached and now - cached[0] < self.FRED_CACHE_TTL:
            return cached[1]

        text = await self._download_fred_series(series_id)
        if not text:
            return None

        reader = csv.reader(StringIO(text))
        next(reader, None)
        samples: list[tuple[str, float]] = []
        for row in reader:
            if len(row) < 2:
                continue
            value = self._safe_float(row[1])
            if value is None:
                continue
            samples.append((row[0], float(value)))

        if not samples:
            return None

        latest = samples[-1]
        prev = samples[-2] if len(samples) > 1 else None
        payload = {
            "date": latest[0],
            "value": latest[1],
            "previous": prev[1] if prev else None,
        }
        self._fred_cache[series_id] = (now, payload)
        return payload

    async def _download_fred_series(self, series_id: str) -> str | None:
        start = (datetime.utcnow() - timedelta(days=self.FRED_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        params = {"id": series_id, "cosd": start}
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                    resp = await client.get(self.FRED_ENDPOINT, params=params)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                logger.warning(
                    "FRED request for %s failed (attempt %s/%s): %s",
                    series_id,
                    attempt,
                    self.MAX_RETRIES,
                    exc,
                )
                await asyncio.sleep(0.3 * attempt)
        return None

    async def _fetch_calendar_feed(self) -> list[Mapping[str, Any]]:
        now = time.time()
        if self._calendar_cache and now - self._calendar_cache[0] < self.CALENDAR_CACHE_TTL:
            cached = self._filter_future_events(self._calendar_cache[1])
            if cached:
                return cached

        events = await self._fetch_nasdaq_calendar()
        if not events:
            events = await self._fetch_fxstreet_calendar()
        if not events:
            events = await self._fetch_forexfactory_calendar()
        if not events:
            events = await self._fetch_tradingeconomics_calendar()

        events = self._filter_future_events(events)
        if events:
            self._calendar_cache = (now, events)
            return events

        if self._calendar_cache:
            cached = self._filter_future_events(self._calendar_cache[1])
            if cached:
                return cached
        return []

    def _filter_future_events(self, events: list[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
        if not events:
            return []
        now = datetime.now(timezone.utc)
        grace = now - timedelta(hours=1)
        horizon = now + timedelta(days=self.CALENDAR_LOOKAHEAD_DAYS)
        filtered: list[Mapping[str, Any]] = []
        for event in events:
            dt = self._parse_event_datetime(event.get("datetime"))
            if not dt:
                continue
            if dt.tzinfo:
                dt_utc = dt.astimezone(timezone.utc)
            else:
                dt_utc = dt.replace(tzinfo=timezone.utc)
            if grace <= dt_utc <= horizon:
                filtered.append(event)
        return filtered

    def _parse_event_datetime(self, raw_ts: Any) -> datetime | None:
        if isinstance(raw_ts, datetime):
            return raw_ts
        if isinstance(raw_ts, str):
            try:
                return datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except Exception:
                return None
        return None

    async def _fetch_forexfactory_calendar(self) -> list[Mapping[str, Any]]:
        if self._forexfactory_backoff_until and time.time() < self._forexfactory_backoff_until:
            logger.debug(
                "ForexFactory calendar still in cooldown for %.1f seconds",
                self._forexfactory_backoff_until - time.time(),
            )
            return []

        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                resp = await client.get(self.CALENDAR_ENDPOINT)
        except Exception as exc:
            logger.warning("ForexFactory calendar fetch failed: %s", exc)
            return []

        if resp.status_code == 429:
            self._forexfactory_backoff_until = time.time() + self.FOREXFACTORY_COOLDOWN_TTL
            logger.warning(
                "ForexFactory calendar is throttling (429). Cooldown until %s",
                datetime.utcfromtimestamp(self._forexfactory_backoff_until).isoformat(),
            )
            return []

        try:
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.warning("ForexFactory calendar returned invalid payload: %s", exc)
            return []

        self._forexfactory_backoff_until = 0.0
        if not isinstance(payload, list):
            return []

        events: list[Mapping[str, Any]] = []
        for raw_event in payload[:100]:
            date_str = raw_event.get("date")
            timestamp: str | None = None
            if isinstance(date_str, str):
                try:
                    timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
                except Exception:
                    timestamp = None
            title = raw_event.get("title") or raw_event.get("event") or "事件"
            event_id = raw_event.get("id") or f"FF-{(title or 'event')}-{date_str or ''}"
            events.append(
                {
                    "event_id": event_id,
                    "title": title,
                    "country": raw_event.get("country"),
                    "datetime": timestamp,
                    "importance": raw_event.get("impact"),
                    "forecast": raw_event.get("forecast"),
                    "previous": raw_event.get("previous"),
                    "source": "ForexFactory",
                }
            )
        return events

    async def _fetch_tradingeconomics_calendar(self) -> list[Mapping[str, Any]]:
        start = datetime.utcnow().date()
        end = start + timedelta(days=self.TRADING_ECONOMICS_LOOKAHEAD_DAYS)
        url = (
            f"{self.TRADING_ECONOMICS_ENDPOINT}"
            f"?c={self.TRADING_ECONOMICS_CREDENTIALS}"
            f"&format=json&d1={start.isoformat()}&d2={end.isoformat()}"
        )
        payload = await self._http_get_json(url)
        if not isinstance(payload, list):
            return []

        importance_map = {"1": "Low", "2": "Medium", "3": "High"}
        events: list[Mapping[str, Any]] = []
        for raw_event in payload[:100]:
            date_str = raw_event.get("Date")
            timestamp: str | None = None
            if isinstance(date_str, str):
                try:
                    timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
                except Exception:
                    timestamp = date_str
            calendar_id = raw_event.get("CalendarId") or raw_event.get("Ticker") or "TE"
            importance_val = raw_event.get("Importance")
            if isinstance(importance_val, (int, float)):
                importance_key = str(int(importance_val))
            else:
                importance_key = str(importance_val or "")
            events.append(
                {
                    "event_id": f"TE-{calendar_id}",
                    "title": raw_event.get("Event") or raw_event.get("Category") or "事件",
                    "country": raw_event.get("Country"),
                    "datetime": timestamp,
                    "importance": importance_map.get(importance_key, importance_val),
                    "forecast": raw_event.get("Forecast") or raw_event.get("TEForecast"),
                    "previous": raw_event.get("Previous"),
                    "source": "TradingEconomics",
                }
            )
        return events

    async def _fetch_fxstreet_calendar(self) -> list[Mapping[str, Any]]:
        now = time.time()
        if self._fxstreet_cache and now - self._fxstreet_cache[0] < self.FXSTREET_CACHE_TTL:
            return list(self._fxstreet_cache[1])

        text = await self._http_get_text(self.FXSTREET_CALENDAR_URL, trust_env=False)
        if not text:
            text = await self._http_get_text(self._wrap_proxy(self.FXSTREET_CALENDAR_URL), trust_env=False)
        if not text:
            return []

        events: list[Mapping[str, Any]] = []
        current_date: str | None = None
        current_year = datetime.utcnow().year
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 1 and "," in cells[0]:
                current_date = cells[0]
                continue
            if not current_date or len(cells) < 4 or not cells[0]:
                continue
            if not re.match(r"\d", cells[0]):
                continue
            dt = self._parse_fxstreet_datetime(current_date, cells[0], current_year)
            if not dt:
                continue
            currency = cells[2] or "--"
            title = cells[3] or "事件"
            actual = cells[5] if len(cells) > 5 else ""
            consensus = cells[7] if len(cells) > 7 else ""
            previous = cells[8] if len(cells) > 8 else ""
            events.append(
                {
                    "event_id": f"FXS-{hash((title, dt.isoformat(), currency))}",
                    "title": title,
                    "country": currency,
                    "datetime": dt.isoformat(),
                    "importance": "",
                    "actual": actual if actual not in {"-", "", "locked"} else None,
                    "forecast": consensus if consensus not in {"-", ""} else None,
                    "previous": previous if previous not in {"-", ""} else None,
                    "source": "FXStreet",
                }
            )
            if len(events) >= self.FXSTREET_MAX_EVENTS:
                break

        self._fxstreet_cache = (now, events)
        return events

    async def _fetch_nasdaq_calendar(self) -> list[Mapping[str, Any]]:
        today = datetime.utcnow().date()
        tasks = []
        for offset in range(self.NASDAQ_LOOKAHEAD_DAYS):
            date_obj = today + timedelta(days=offset)
            params = {"date": date_obj.isoformat()}
            tasks.append(
                asyncio.create_task(
                    self._http_get_json(
                        self.NASDAQ_CALENDAR_ENDPOINT,
                        params=params,
                        headers=self.NASDAQ_HEADERS,
                    )
                )
            )

        events: list[Mapping[str, Any]] = []
        for offset, task in enumerate(tasks):
            payload = await task
            if not isinstance(payload, Mapping):
                continue
            data = payload.get("data") or {}
            rows = data.get("rows")
            if not isinstance(rows, list):
                continue
            event_date = today + timedelta(days=offset)
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                parsed = self._parse_nasdaq_event(event_date, row)
                if parsed:
                    events.append(parsed)
        return events

    def _parse_nasdaq_event(self, event_date: datetime.date, row: Mapping[str, Any]) -> Mapping[str, Any] | None:
        time_str = str(row.get("gmt") or "").strip()
        timestamp: datetime | None = None
        if time_str:
            if time_str.upper() == "24H":
                timestamp = datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc)
            else:
                try:
                    tm = datetime.strptime(time_str, "%H:%M").time()
                    timestamp = datetime.combine(event_date, tm, tzinfo=timezone.utc)
                except Exception:
                    timestamp = datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc)
        else:
            timestamp = datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc)

        title = row.get("eventName") or row.get("event") or "事件"
        country = row.get("country") or row.get("countryCode")
        event_id = f"NAS-{hash((event_date.isoformat(), title, country or ''))}"
        return {
            "event_id": event_id,
            "title": title,
            "country": country,
            "datetime": timestamp.isoformat() if timestamp else None,
            "importance": row.get("impact") or row.get("importance"),
            "actual": self._clean_text_field(row.get("actual")),
            "forecast": self._clean_text_field(row.get("consensus")),
            "previous": self._clean_text_field(row.get("previous")),
            "source": "Nasdaq",
        }

    def _clean_text_field(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _parse_fxstreet_datetime(self, date_label: str, time_str: str, year: int) -> datetime | None:
        try:
            base_date = datetime.strptime(f"{date_label} {year}", "%A, %B %d %Y")
        except Exception:
            return None
        ts = time_str.strip()
        if not ts:
            return None
        if ts.lower() == "all day":
            return datetime(base_date.year, base_date.month, base_date.day, tzinfo=timezone.utc)
        try:
            time_part = datetime.strptime(ts, "%I:%M %p").time()
        except Exception:
            return None
        return datetime.combine(base_date.date(), time_part, tzinfo=timezone.utc)

    def _wrap_proxy(self, url: str) -> str:
        return f"https://r.jina.ai/{url}"

    def _extract_json_from_text(self, text: str) -> Any | None:
        if not text:
            return None
        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except Exception:
                pass
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(stripped[start : end + 1])
            except Exception:
                return None
        return None

    def _merge_by_recency(
        self,
        base: Mapping[str, Any],
        incoming: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged = dict(base)
        for code, snapshot in incoming.items():
            if not isinstance(snapshot, Mapping):
                continue
            existing = merged.get(code)
            if not existing:
                merged[code] = snapshot
                continue
            existing_ts = self._parse_iso_timestamp(existing.get("timestamp"))
            incoming_ts = self._parse_iso_timestamp(snapshot.get("timestamp"))
            if incoming_ts and (not existing_ts or incoming_ts > existing_ts):
                merged[code] = snapshot
        return merged

    def _parse_iso_timestamp(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
        return None

    def _parse_goldprice_timestamp(self, raw: Any) -> str | None:
        if not isinstance(raw, str) or not raw:
            return None
        # Example: "Nov 22nd 2025, 10:38:05 am NY"
        try:
            cleaned = raw.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
            dt = datetime.strptime(cleaned, "%b %d %Y, %I:%M:%S %p %Z")
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            return None

    async def _fetch_fred_commodities(self) -> dict[str, Any]:
        tasks = {
            series_id: asyncio.create_task(self._get_fred_series(series_id))
            for series_id in self.FRED_COMMODITY_SERIES
        }
        payload: dict[str, Any] = {}
        for series_id, task in tasks.items():
            data = await task
            if not data:
                continue
            code, label, decimals = self.FRED_COMMODITY_SERIES[series_id]
            latest = data["value"]
            prev = data.get("previous")
            change = (latest - prev) if prev is not None else 0.0
            payload[code] = {
                "code": code,
                "name": label,
                "display_name": label,
                "last": round(latest, decimals),
                "change": round(change, decimals),
                "change_pct": round((change / prev * 100) if prev else 0.0, 2),
                "timestamp": data.get("date") or datetime.utcnow().isoformat(),
                "source": "fred",
            }
        return payload
