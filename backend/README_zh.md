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

### 数据提供方与模式
- `DATA_MODE=mock`：返回静态快照，适合脱网联调。
- `DATA_MODE=open`：聚合腾讯行情（指数/美股）+ Stooq 兜底、Yahoo 期货（WTI/布油/铜/天然气/贵金属/农产品等）、财政部/中国债券信息网国债曲线（经 `r.jina.ai` 代理抓取 1Y/3Y/5Y/10Y）、FRED（SOFR/UST）、CoinGecko 加密资产、FXStreet 宏观事件等。如需更高配额，可设置 `ALPHAVANTAGE_API_KEY`。
- `DATA_MODE=wind`：依赖 WindPy/WAPI，请参考 `docs/notes/wind_integration_status.md` 提供的代码映射与注意事项。

常用环境变量：
- `SNAPSHOT_CACHE_TTL`：内存快照缓存时间（秒）。
- `REDIS_ENABLED` / `REDIS_URL`：启用 Redis 缓存时的连接信息。
- `REQUEST_TIMEOUT` 等参数在 `OpenProvider` 中定义，可按照需要调整。

### 基本健康检查
- 存活探针：`/health/live`
- 就绪探针：`/health/ready`，返回数据模式与缓存状态。

### 快照缓存
- 通过 `REDIS_ENABLED=true` 和 `REDIS_URL=redis://host:port/db` 进行切换。
- 缓存 TTL 由 `SNAPSHOT_CACHE_TTL`（秒）控制。

### 开放模式手工验收

```bash
DATA_MODE=open uv run uvicorn app.main:app
curl -s http://localhost:8000/data/latest | jq '.data_mode, .timestamp'
```

配合仓库根目录 `deployment/launcher/start_open_wallboard.sh` 可以快速拉起后端 + 静态前端，适合在 WSL/VM 中肉眼检查持续可用性。
