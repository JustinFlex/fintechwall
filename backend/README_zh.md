# Wind 市场信息墙后端

基于 FastAPI 的服务，负责聚合市场数据并向信息亭客户端提供快照。

## 结构
- `app/core`: 配置和共享实用程序。
- `app/api`: FastAPI 路由。
- `app/providers`: 数据源的接口和实现。
- `app/services`: 组合提供商数据的编排层。

## 使用 uv 进行本地开发
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

配置通过环境变量控制；有关默认值，请参阅 `app/core/settings.py`。

### 快照缓存
- 通过 `REDIS_ENABLED=true` 和 `REDIS_URL=redis://host:port/db` 进行切换。
- 缓存 TTL 由 `SNAPSHOT_CACHE_TTL`（秒）控制。