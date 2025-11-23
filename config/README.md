# Configuration Templates

This directory stores configuration samples shared by both backend and frontend runtimes.

- `defaults/session_schedule.yaml`: default carousel dwell weights per trading session.
- `defaults/refresh_intervals.yaml`: polling/WebSocket refresh cadence guidance.
- `defaults/backend.env`: .env template describing data provider mode (`mock/wind/open`) and Redis snapshot cache options.

Runtime services should copy relevant files into their environment-specific configuration and may override values through environment variables or admin tooling.
