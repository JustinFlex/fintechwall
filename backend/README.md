# Wind Market Wallboard Backend

FastAPI-based service responsible for aggregating market data and serving snapshots to the kiosk client.

## Structure
- `app/core`: configuration and shared utilities.
- `app/api`: FastAPI routers.
- `app/providers`: interfaces and implementations for data sources.
- `app/services`: orchestration layers combining provider data.

## Local Development with uv
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Configuration is controlled via environment variables; see `app/core/settings.py` for defaults.

### Health checks
- Liveness: `/health/live`
- Readiness: `/health/ready` (includes data mode and cache status).

### Snapshot Caching
- Toggle via `REDIS_ENABLED=true` and `REDIS_URL=redis://host:port/db`.
- Cache TTL governed by `SNAPSHOT_CACHE_TTL` (seconds).
