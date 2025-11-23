# Wind Market Wallboard – Technical Architecture (Python + HTML Front-End)

## 1. Architecture Overview
The system is a data-driven kiosk application composed of a Python backend and a standards-based HTML/CSS/JavaScript front-end. It aggregates multi-asset market data, normalises it into a unified schema, and streams it to a browser-based carousel for passive viewing. Two deployment modes (Wind Edition and Open Edition) share the same architecture with pluggable data providers.

## 2. System Context
- **External Systems**: WindPy/WAPI servers, public market data APIs (Yahoo, FRED, ECB, CoinGecko, Binance, etc.), RSS/Atom feeds.
- **Internal Components**: Data ingestion service, real-time stream service, cache (Redis), REST/WebSocket API, static front-end served via Python web server (e.g., FastAPI + Starlette static files), kiosk client (Chromium running in kiosk mode).
- **Stakeholders**: Operators (set configuration), Viewers (consume passive display), DevOps (monitor services).

## 3. Requirements Traceability
- Supports requirements from PRD: multi-scene carousel, dual data editions, refresh cadence, accessibility, kiosk reliability, fallback logic. Each component is designed to meet these functional and non-functional criteria.

## 4. Component Architecture
### 4.1 Backend Services (Python)
- **API Gateway**: FastAPI application exposing REST endpoints (`/data/latest`, `/calendar`, `/status`) and WebSocket channels (`/ws/stream`). Serves static HTML/JS/CSS assets for front-end.
- **Data Ingestion Workers**:
  - Scheduled tasks managed by APScheduler or Celery Beat, running within Python service cluster.
  - Fetch data per asset class using provider interfaces; normalise data and write to Redis.
- **Provider Abstraction Layer**:
  - Interface `MarketDataProvider` with methods `fetch_indices()`, `fetch_fx()`, `fetch_rates()`, etc.
  - Implementations: `WindProvider` (WindPy), `OpenProvider` (public APIs).
  - Configurable per metric to allow hybrid mode (e.g., Wind for equities, open source for crypto).
- **Realtime Stream Manager**:
  - Async tasks using `asyncio` + `websockets`/`aiohttp` to consume Binance/OKX streams.
  - Maintains in-memory state, pushes updates to Redis and broadcasts to clients via WebSocket.
- **Caching Layer**: Redis stores latest payloads keyed by edition and scene; includes TTL metadata and last-update timestamps.
- **Persistence**: Optional local file store (JSON snapshots) for warm restart when cache unavailable.

### 4.2 Front-End (HTML/CSS/JavaScript)
- Static HTML shell rendered by the Python server; assets built from modular JS (ES modules) and CSS (Tailwind or custom utility classes) compiled via a lightweight build step (e.g., Vite or Parcel) producing static files.
- **Carousel Engine**: Vanilla JS module controlling scene rotation, dwell timers, session scheduling, and fail-safe freeze when data stale.
- **Data Layer**: Fetches initial snapshot via REST, subscribes to WebSocket for live updates, merges into state store (simple `EventTarget` or minimal store pattern).
- **Scenes**: Template-driven HTML components per scene using DOM manipulation (no heavy framework). Lightweight charting via open-source libraries (TradingView Lightweight Charts or Apache ECharts) embedded via script.
- **Marquee & Ticker**: CSS animations for scrolling tickers; responsive scaling to 4K.
- **Offline Handling**: Service worker or JS polling to detect disconnect, display cached data with stale indicators.

### 4.3 Deployment & Infrastructure
- Containerised Python service (FastAPI + workers) packaged with dependencies (`windpy` optional dependency group, `requests`, `aiohttp`, `redis`, `apscheduler`).
- Redis deployed either alongside via Docker container or managed service.
- Nginx (optional) as reverse proxy for TLS termination and static caching.
- Kiosk device runs Chromium pointing to service URL; systemd service ensures browser autostart.

## 5. Data Flow
1. Scheduler triggers provider fetch (e.g., `fetch_indices`).
2. Provider queries primary API (Wind or open) and receives data payload.
3. Normaliser maps fields to canonical schema, adds edition metadata, writes to Redis.
4. API Gateway exposes `/data/latest` endpoint reading from Redis; watchers subscribe to `/ws/stream` for push updates.
5. Front-end loads initial HTML, fetches latest data, and begins carousel. WebSocket updates refresh DOM without full reload.
6. If provider fetch fails, fallback logic attempts secondary source; on repeated failure, stale flag set and surfaced to front-end.

## 6. Data Providers
### 6.1 Wind Edition
- Uses `WindPy` synchronous API for `wsq`, `wsi`, `wsd`, macro calendar endpoints.
- Python service manages Wind session lifecycle (`w.start()`, heartbeats, reconnection on failure).
- Data mapping layer converts Wind codes (e.g., `SPX.GI`) to friendly IDs.

### 6.2 Open Edition
- Providers implemented using HTTP APIs:
  - Yahoo Finance/Stooq for indices and equities.
  - FRED, U.S. Treasury, ECB, MAS for rates.
  - CoinGecko for crypto (REST) plus Binance/OKX WebSocket.
  - CBOE CSV for implied vol, CME FedWatch CSV for probabilities.
  - RSS ingestion via feedparser for news.
- Rate limiting handled via request throttling and caching layer (ETag, `If-Modified-Since`).
- Error wrapping ensures consistent exception handling across providers.

## 7. Configuration & Secrets
- `config.yaml` or environment variables specify edition mode, refresh intervals, session schedule, API keys.
- Secrets stored via environment variables or secret manager (for Wind credentials, API keys like AlphaVantage).
- Configuration loaded at startup; dynamic reload optional via admin endpoint.

## 8. Non-Functional Requirements
- **Performance**: Backend should handle <500 ms response time for snapshot API; WebSocket broadcasts within 1 second of receiving update.
- **Reliability**: Automatic reconnection and exponential backoff for all external connections. Health checks for ingestion, stream, and API services.
- **Scalability**: Designed for single kiosk use but scalable horizontally by running multiple Python workers sharing Redis.
- **Security**: HTTPS termination; restrict admin endpoints; ensure CORS limited to kiosk origins; sanitize RSS/news content.
- **Maintainability**: Clear separation of provider modules; unit tests around data transforms; logging using structured JSON (e.g., `structlog`).

## 9. Data Storage & Schema
- Redis keys: `wallboard:{edition}:{scene}` storing JSON payloads; TTL set per scene.
- Snapshot file (optional) stored locally as `snapshots/{edition}-{timestamp}.json`.
- Schema defined in shared Python dataclasses (`pydantic` models) for validation.

## 10. Monitoring & Observability
- Prometheus metrics exported from FastAPI (request latency, error counts).
- Custom metrics: data freshness age per metric, WebSocket client connections, provider failure counts.
- Alerting thresholds for SLA breaches (e.g., FX data older than 30 seconds).
- Log aggregation via ELK or Loki stack.

## 11. Deployment Pipeline
- CI/CD pipeline runs tests, builds static assets, lints Python (ruff) and JS (eslint), builds Docker images.
- Separate build targets for Wind and Open editions (Wind build includes `windpy` dependency, open build excludes).
- Versioned releases with migration scripts (if schema changes) and documentation updates.

## 12. Operational Runbook (Summary)
1. **Startup**: Launch Redis -> start Python service -> verify health endpoints -> start kiosk browser.
2. **Edition Switch**: Update environment variable `DATA_MODE`, restart Python service, verify provider connectivity.
3. **Incident Handling**: Check logs for provider failures, confirm fallbacks triggered, notify stakeholders if data gap > SLA.
4. **Updates**: Pull latest container, run migrations if any, restart services during maintenance window.

## 13. Future Enhancements
- Optional admin dashboard for real-time monitoring and manual overrides.
- Integration with message queue (e.g., Kafka) for scaling to multiple wallboards.
- Extend open edition with community-sourced datasets (e.g., GitHub data dumps) for sector weights.
- Consider server-side rendering of fallback PNG slides for environments with limited browsers.
