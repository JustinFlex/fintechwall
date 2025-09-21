# Deployment Strategies

This module documents two supported deployment modes for the Wind Market Wallboard backend + frontend stack:

1. **uv-managed native install** – for bare-metal or VM targets where Python 3.11+ is available. Uses `uv` to reproduce environments. See `uv/README.md`.
2. **Docker Compose bundle** – containerised deployment with Redis caching, backend API, and static frontend server. See artifacts under `docker/`.

Each mode shares config templates from `../config` and expects Wind credentials or open API keys to be provisioned separately.

> Note: the frontend is currently a static bundle; integration with backend API base URL is handled client-side via `window.__WALLBOARD_API__`. Future revisions may add dynamic config injection.
