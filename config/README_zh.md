# 配置模板

此目录存储后端和前端运行时共享的配置示例。

- `defaults/session_schedule.yaml`: 每个交易时段的默认轮播停留权重。
- `defaults/refresh_intervals.yaml`: 轮询/WebSocket 刷新频率指南。
- `defaults/backend.env`: `.env` 模板，列出了数据源模式（`mock/wind/open`）以及 Redis 缓存开关等关键环境变量。

运行时服务应将相关文件复制到其特定于环境的配置中，并可以通过环境变量或管理工具覆盖值。
