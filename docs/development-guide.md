# Wind Market Wallboard – Development Guide

## 1. Overview & Scope
- **Goal**: Deliver a 1-minute looping, multi-scene market intelligence wallboard that gives an instant snapshot of global markets.
- **Form Factor**: 16:9 4K horizontal display (55–65″) running in kiosk mode, auto-start and auto-reconnect.
- **Scene Rotation**: Five scenes (A–E) cycling every 20–45 seconds; full loop ≤ 60 seconds. Order and dwell times adjust to the active trading session.
- **Target Users**: Trading desks, classrooms, or briefing rooms that need fast situational awareness without manual interaction.
- **Variants**:
  - **Wind Edition** – Uses WindPy/WAPI as the authoritative data source with open/free feeds as backups.
  - **Open Edition** – Uses only non-commercial open or free APIs; must be deployable without Wind access while preserving the same UI/UX experience.

## 2. Product Variants
### 2.1 Shared Principles
- Identical user experience, layout, and scene logic across editions.
- Unified payload schema so the frontend and carousel logic remain unchanged.
- Edition chosen via configuration (`DATA_MODE=wind|open`) with per-metric overrides for testing.
- Both editions maintain Redis caches keyed by `source`, enabling parallel operation.

### 2.2 Wind Edition
- **Primary Sources**: WindPy/WAPI for global indices, futures main contracts, FX, rates, macro calendar, industry classifications, and implied volatility metrics.
- **Fallbacks**: Public APIs where permissible (e.g., CoinGecko for crypto, FRED for US yields).
- **Credential Handling**: Requires Wind terminal credentials; schedule keep-alive heartbeats to prevent session expiry.

### 2.3 Open Edition
- **Primary Sources**: Public/non-commercial data providers such as Yahoo Finance, Stooq, Twelve Data, ECB, AlphaVantage, FRED, U.S. Treasury, MAS, CME FedWatch CSV, CoinGecko, Binance/OKX, and official RSS feeds.
- **Constraints**: Observe attribution/licensing requirements; some endpoints have rate limits or delayed data.
- **Fallbacks**: Alternative free feeds or cached last-known values to preserve parity with Wind Edition.

## 3. Scene Requirements
### Scene A – Global Overview (Now)
- **Content**:
  - Equities: S&P 500, Nasdaq 100, Euro Stoxx 50, Nikkei 225, Hang Seng, SSE 50, NIFTY 50, STI.
  - Commodities/Energy: WTI, Brent, Gold, Silver, Copper, Iron Ore (main contract).
  - FX: DXY, USD/JPY, EUR/USD, USD/CNH, USD/SGD.
  - Rates: US 2Y & 10Y, Germany 10Y, Japan 10Y, Singapore 10Y, plus 2s10s inversion flag.
  - Crypto: BTC, ETH, SOL price & 24h change, USDT/USDC dominance.
  - Market Status: Exchange open/closed indicator with local time and Singapore time.
- **Wind Edition Sources**: Wind `wsq`/`wsd`/`wsi` endpoints.
- **Open Edition Sources**: Yahoo Finance or Stooq for indices, CME/Quandl/EIA for commodities, ECB & AlphaVantage for FX, FRED/Treasury/MAS for rates, CoinGecko for crypto.

### Scene B – Equity Heat
- **Heatmap**: Global or regional (US/EU/APAC) heatmap where colour = daily return, size = turnover or weight.
- **Movers List**: Top 10 gainers/losers with liquidity filter (market cap & volume thresholds).
- **Volatility Panel**: VIX, VXN values plus 1M vs 3M implied vol term-structure mini-chart.
- **Wind Edition Sources**: Wind industry classifications & turnover data, implied vol indices via Wind.
- **Open Edition Sources**: ETF holdings datasets, public sector benchmarks, Stooq/Yahoo volume, CBOE published VIX/VXN (delayed) and public term-structure CSVs.

### Scene C – Macro & Rates
- **Yield Curves**: US, Germany, Japan, Singapore curves with comparison shading versus prior week.
- **Policy Expectations**: CME Fed Funds futures–implied probabilities for next FOMC meeting.
- **Reference Rates**: SOFR, SORA (and optional SHIBOR for context).
- **Economic Calendar**: Upcoming 24–72 hour events with countdown, previous/consensus/actual fields.
- **Wind Edition Sources**: Wind macro calendar, yield curves, and reference rates.
- **Open Edition Sources**: U.S. Treasury daily yield curve, ECB/Deutsche Bundesbank releases, Japan MOF, MAS/ABS for SORA/SOR, CME FedWatch CSV, Investing.com/ForexFactory RSS or iCal feeds (subject to terms).

### Scene D – Crypto Depth
- **Spot Metrics**: BTC/ETH/SOL price, 24h change, and annualised realised volatility snapshot.
- **Derivatives**: Perpetual funding rates and open interest (aggregate view) from major exchanges.
- **Stablecoin Flows**: Net flows to/from exchanges for USDT/USDC.
- **On-Chain Activity**: 1–2 metrics (e.g., active addresses, transfer volume).
- **Sources**: CoinGecko REST for spot/vol; Binance, OKX, Coinbase WebSocket streams for funding & open interest; public on-chain APIs (Glassnode community endpoints or self-computed) – applies to both editions.

### Scene E – News Banner (Optional)
- **Content**: Headline-only ticker for central bank remarks, major earnings, scheduled events; optional event countdown substitute.
- **Licensing**: No article bodies. Use official RSS feeds (central banks, exchanges, Reuters/Yahoo headline feeds) or rely on calendar events to avoid copyright issues.
- **Wind Edition**: Wind headline feeds if contractual rights permit.
- **Open Edition**: RSS/Atom ingestion with attribution.

### Scene Timing & Weighting
- Default rotation ≤ 60 seconds; scene dwell time configurable per session.
- Sessions:
  - Asia (07:00–13:00 SGT): emphasise APAC equities & rates.
  - Europe (13:00–20:00 SGT): emphasise Euro assets.
  - US (20:00–02:00 SGT): emphasise US equities, treasuries, crypto.
  - Overnight (02:00–07:00 SGT): prioritise macro calendar and crypto.
- If data stale beyond SLA, hold current scene with “Last updated HH:MM” badge while retrying refresh.

## 4. User Experience & Layout
- **Grid**: Three-column layout plus top marquee.
  - Top: scrolling ticker cycling indices, FX, commodities, crypto highlights.
  - Left: hero price cards (≥ 60–80 px numerics) with ▲▼ glyphs.
  - Center: heatmap or mini charts (sparklines, candlesticks).
  - Right: yield summaries, funding rates, calendar tiles.
- **Design Language**: Blue/orange palette for colour-blind friendliness; high-contrast sparklines; limited gridlines.
- **Market Status**: Small green/grey dot plus local and SGT time.
- **Interaction**: Kiosk mode, no user controls, auto dark mode after preset time.
- **Accessibility**: Use typefaces optimised for distance readability; maintain contrast ratios per WCAG AA.

## 5. Data Source Matrix
| Metric | Wind Edition Primary | Wind Edition Fallback | Open Edition Primary | Open Edition Fallback | Notes |
| --- | --- | --- | --- | --- | --- |
| Global indices | Wind `wsq` | Yahoo Finance API | Yahoo Finance / Stooq | Twelve Data / Tiingo (freemium) | Check rate limits & licensing |
| Futures & commodities | Wind `wsd` (main contracts) | Quandl (CME), EIA | Quandl free datasets, CME CSV | Investing.com scrape (if terms allow) | Iron ore via DCE main contract; verify availability |
| FX snapshot | Wind real-time | ECB reference rates | ECB reference, AlphaVantage FX | Dukascopy JSON | Convert to SGT; note delay |
| Rates & curves | Wind yield endpoints | FRED / Treasury | Treasury, ECB, MAS | Investing.com CSV | Compute curve interpolation if needed |
| Econ calendar | Wind calendar | Manual CSV | Investing.com / ForexFactory feeds | Custom curated Google Sheet | Validate copyright |
| Sector data | Wind industry tree | ETF holdings CSV | GICS-equivalent from public ETFs | Manual mapping | Precompute for heatmap |
| Implied vol | Wind indices | CBOE CSV | CBOE published data | AlphaVantage volatility series | Delayed quotes acceptable |
| Crypto spot | CoinGecko | Binance REST | CoinGecko | Coinbase REST | Shared across editions |
| Funding & OI | Binance/OKX WebSocket | Deribit WebSocket | Binance/OKX WebSocket | Coinalyze (if allowed) | Aggregate per exchange |
| Stablecoin flows | Calculated (Wind auxiliary) | Glassnode (paid) | On-chain APIs (e.g., CryptoQuant free, Nansen lite) | Self-computed ETL | Consider building ETL |
| News headlines | Wind news (if licensed) | RSS feeds | RSS/Atom feeds | Calendar events | Store only title, time, source |

## 6. System Architecture
### 6.1 High-Level Components
- **Data Ingestion Service (Python)**:
  - Runs Wind adaptor (Wind Edition) or open-source adaptor (Open Edition).
  - Schedules pull jobs by asset class; normalises to shared schema.
  - Writes payloads into Redis with versioning and timestamps.
- **Realtime Stream Service (Node/TypeScript)**:
  - Manages WebSocket subscriptions (crypto, high-frequency FX).
  - Aggregates streams, applies backoff, and broadcasts consolidated WebSocket to frontend.
- **REST/GraphQL API**: Exposes cached snapshots for low-frequency data (calendar, heatmap).
- **Frontend (React + Vite + Tailwind)**:
  - Renders scenes, handles carousel timing, kiosk full-screen, offline cache.
  - Consumes REST/WebSocket endpoints agnostic of edition.
- **Configuration Module**:
  - Environment-driven edition toggle, session schedules, refresh intervals.
- **Monitoring & Logging**:
  - Structured logs with source metadata, latency, and error codes.
  - Health endpoints per service; optional Grafana dashboards.

### 6.2 Deployment
- Containerised services orchestrated via Docker Compose or Kubernetes (optional).
- Kiosk hosts (mini PC / Raspberry Pi) run Chromium in kiosk mode with auto-start scripts.
- Persistent volume for cached payloads to enable warm restart when network is down.

## 7. Data Refresh & Resilience
- **Refresh Cadence**:
  - Spot FX & crypto: 5–15 seconds.
  - Rates, implied vol, heatmap: 1–5 minutes.
  - Economic calendar: 60 minutes when upcoming, 1–5 minutes within 2 hours of event.
  - News ticker: 30–60 seconds.
- **Fallback Workflow**:
  1. Attempt primary source within SLA.
  2. On timeout, call fallback source.
  3. If fallback fails, surface cached value with “stale” badge and timestamp.
- **Error Handling**:
  - Detect abnormal values (z-score thresholds) and clamp or flag.
  - Expose last successful update time in API responses.
- **Persistence**:
  - Store last payload to disk; load on startup.
  - Keep per-scene TTL configuration to avoid over-fetching.

## 8. Data Modeling
- **Canonical Payload** (JSON):
  - `indices`, `commodities`, `fx`, `rates`, `crypto`, `calendar`, `heatmap`, `volTerm`, `stablecoinFlows`, `news`, `metadata`.
  - Each entry includes `code`, `label`, `value`, `changePct`, `timestamp`, `source`.
  - `metadata` includes edition (`wind`/`open`), refresh timestamps, licence notes.
- **Historical Arrays**: Provide mini-series (`spark`) arrays for sparklines and term-structure visualisations.
- **Calendar Items**: `event`, `importance`, `time_local`, `time_sgt`, `previous`, `consensus`, `actual`, `status` (`upcoming|released`).
- **Heatmap Model**: Hierarchical sectors → industries → tickers with `weight`, `changePct`, `turnover`.

## 9. Implementation Roadmap
1. **Foundation**
   - Set up repo structure, common config, Redis instance.
   - Implement provider abstraction with Wind and Open implementations for Scene A metrics.
2. **Data Coverage Expansion**
   - Add modules for Scenes B–E data; wire crypto WebSocket aggregation.
   - Implement fallback chains and caching policies.
3. **Frontend MVP**
   - Build layout grid, marquee, scene shells, and carousel controller with mock data.
4. **Visual Enhancements**
   - Integrate Lightweight Charts/ECharts for heatmaps/yield curves/vol term structures.
   - Add stablecoin flow visualisations and risk alert banner (e.g., VIX or 2s10s inversion).
5. **Session Scheduling & Theming**
   - Implement time-of-day weighting, auto dark mode, and kiosk preferences.
6. **Resilience & Monitoring**
   - Simulate API outages; verify fallback behaviour; add logging/alerts.
7. **Packaging & Delivery**
   - Create deployment scripts, kiosk autostart configs, and admin documentation.

## 10. Testing & Validation
- **Unit Tests**: Provider adaptors, schema validation, conversion utilities.
- **Integration Tests**: Fetch → normalise → cache flows for both editions using mocked API responses.
- **UI Tests**: Snapshot tests for scene layouts, visual regression checks.
- **Failover Tests**: Simulate primary source outage (Wind server down, API rate limit) to ensure fallback and stale indicators fire.
- **Performance Tests**: Verify WebSocket throughput and browser rendering at 4K.

## 11. Operational Considerations
- **Credentials**: Securely store Wind credentials (Wind Edition) and API keys (Open Edition) using environment variables or secrets manager.
- **Attribution**: Display data source disclaimer per edition in a footer or settings overlay.
- **Maintenance**: Schedule job to refresh session schedule rules (holidays) and update symbol lists.
- **Compliance**: Review licences for public APIs to ensure permitted display; maintain audit trail of data usage.

## 12. Risks & Open Questions
- **Licensing**: Confirm redistribution rights for Wind data and for each open API (many forbid commercial display).
- **Data Completeness**: Open Edition may lack certain metrics (e.g., iron ore continuous contract); define acceptable substitutes or explicit omissions.
- **Calendar Reliability**: Open sources can lag; consider manual overrides for critical events.
- **WebSocket Limits**: Ensure Binance/OKX allow long-lived kiosk connections; plan for reconnect/backoff.
- **Edition Drift**: Establish automated regression tests so UI gracefully handles missing metrics in Open Edition.

## 13. Appendices
- **A. Key APIs**:
  - WindPy `wsq`, `wsi`, `wsd`, macro calendar endpoints.
  - CoinGecko `/simple/price`, `/coins/{id}/market_chart`.
  - Binance Futures WebSocket streams (`bookTicker`, `fundingRate`, `openInterest`).
  - FRED `/series/observations` for rates.
  - U.S. Treasury yield curve CSV.
  - ECB reference rates JSON.
  - CBOE VIX/VXN CSV download links.
  - CME FedWatch CSV for probabilities.
- **B. Configuration Samples**:
  ```json
  {
    "dataMode": "wind",
    "sessionSchedule": [
      { "name": "Asia", "start": "07:00", "end": "13:00", "scenes": {"A": 25, "B": 20, "C": 20, "D": 20, "E": 15} },
      { "name": "Europe", "start": "13:00", "end": "20:00", "scenes": {"A": 25, "B": 25, "C": 20, "D": 15, "E": 15} },
      { "name": "US", "start": "20:00", "end": "02:00", "scenes": {"A": 25, "B": 25, "C": 20, "D": 20, "E": 10} },
      { "name": "Overnight", "start": "02:00", "end": "07:00", "scenes": {"A": 20, "B": 15, "C": 30, "D": 25, "E": 10} }
    ],
    "refreshIntervals": {
      "fx": 10,
      "crypto": 10,
      "rates": 120,
      "calendar": 300,
      "news": 45
    }
  }
  ```
- **C. Glossary**:
  - **SLA** – Service Level Agreement for data freshness.
  - **OI** – Open Interest.
  - **SORA/SOFR** – Singapore/US overnight risk-free rates.
  - **2s10s Inversion** – US Treasury 2-year yield minus 10-year yield negative condition triggering risk flag.
