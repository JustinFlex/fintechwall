# uv Deployment Guide

## Prerequisites
- Python 3.11+
- `uv` package manager (`pip install uv` or see https://docs.astral.sh/uv/)
- Redis (optional) if enabling snapshot caching
- Environment variables for Wind/Open API keys/credentials

## Directory Layout
``
projects/wind-wallboard/
  backend/
  frontend/
  deployment/
    uv/
      README.md
      env.example
      run_backend.sh
      serve_frontend.sh
```

## Steps
1. Copy `env.example` to `../backend/.env` and adjust configuration (set `DATA_MODE`, Redis info, credentials).
2. Install backend dependencies:
   ```bash
   cd ../backend
   uv sync
   ```
3. Start the backend API (development mode):
   ```bash
   ./../deployment/uv/run_backend.sh
   ```
4. Serve the static frontend (simple Python HTTP server for kiosk preview):
   ```bash
   ./../deployment/uv/serve_frontend.sh
   ```
5. Configure kiosk browser to load `http://<host>:4173` (default frontend port) and point `window.__WALLBOARD_API__` to backend (default `http://<host>:8000`).

## Notes
- For systemd services, wrap the scripts with appropriate unit files (examples to be added as implementation matures).
- Redis caching is optional; set `REDIS_ENABLED=true` and `REDIS_URL=redis://...` in `.env` when available.
- Wind credentials should be supplied via environment variables or config secrets (not stored in repository).
