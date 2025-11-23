# Deployment Strategies

This module documents two supported deployment modes for the Wind Market Wallboard backend + frontend stack:

1. **uv-managed native install** – for bare-metal or VM targets where Python 3.11+ is available. Uses `uv` to reproduce environments. See `uv/README.md`.
2. **Docker Compose bundle** – containerised deployment with Redis caching, backend API, and static frontend server. See artifacts under `docker/`.

For无人值守的开放数据部署，还提供：

- `systemd/` – 样例服务单元，直接调用 `deployment/uv/*.sh`。
- `monitoring/` – `open_data_probe.sh` 用于 Cron/Prometheus 等环境定期巡检 `/data/latest`。
- `launcher/` – `start_open_wallboard.sh` 一键脚本（终端执行即可同时拉起后端与前端）。
- `docs/ops_playbook_open_zh.md` – 详细的安装、健康检查、监控与排障指南。

Each mode shares config templates from `../config` and expects Wind credentials or open API keys to be provisioned separately.

> Note: the frontend is currently a static bundle; integration with backend API base URL is handled client-side via `window.__WALLBOARD_API__`. Future revisions may add dynamic config injection.
