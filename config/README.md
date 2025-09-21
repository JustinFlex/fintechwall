# Configuration Templates

This directory stores YAML configuration samples shared by both backend and frontend runtimes.

- `defaults/session_schedule.yaml`: default carousel dwell weights per trading session.
- `defaults/refresh_intervals.yaml`: polling/WebSocket refresh cadence guidance.

Runtime services should copy relevant files into their environment-specific configuration and may override values through environment variables or admin tooling.
