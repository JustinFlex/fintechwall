# Wind 市场墙板 – 技术架构 (Python + HTML 前端)

## 1. 架构概述
该系统是一个数据驱动的信息亭应用程序，由 Python 后端和基于标准的 HTML/CSS/JavaScript 前端组成。它聚合多资产市场数据，将其规范化为统一的模式，并将其流式传输到基于浏览器的轮播界面以供被动查看。两种部署模式（Wind 版和开放版）共享相同的架构，但具有可插拔的数据提供程序。

## 2. 系统环境
- **外部系统**: WindPy/WAPI 服务器、公共市场数据 API（雅虎、FRED、ECB、CoinGecko、币安等）、RSS/Atom 源。
- **内部组件**: 数据提取服务、实时流服务、缓存（Redis）、REST/WebSocket API、通过 Python Web 服务器（例如 FastAPI + Starlette 静态文件）提供服务的静态前端、信息亭客户端（在信息亭模式下运行的 Chromium）。
- **利益相关者**: 操作员（设置配置）、查看者（消费被动显示）、DevOps（监控服务）。

## 3. 需求可追溯性
- 支持 PRD 中的需求：多场景轮播、双数据版本、刷新频率、可访问性、信息亭可靠性、回退逻辑。每个组件的设计都旨在满足这些功能性和非功能性标准。

## 4. 组件架构
### 4.1 后端服务 (Python)
- **API 网关**: FastAPI 应用程序，公开 REST 端点（`/data/latest`、`/calendar`、`/status`）和 WebSocket 通道（`/ws/stream`）。为前端提供静态 HTML/JS/CSS 资产。
- **数据提取工作程序**:
  - 由 APScheduler 或 Celery Beat 管理的计划任务，在 Python 服务集群内运行。
  - 使用提供程序接口按资产类别获取数据；规范化数据并写入 Redis。
- **提供程序抽象层**:
  - `MarketDataProvider` 接口，包含 `fetch_indices()`、`fetch_fx()`、`fetch_rates()` 等方法。
  - 实现：`WindProvider` (WindPy)、`OpenProvider` (公共 API)。
  - 可按指标配置，以允许混合模式（例如，股票使用 Wind，加密货币使用开源）。
- **实时流管理器**:
  - 使用 `asyncio` + `websockets`/`aiohttp` 的异步任务，以消费币安/OKX 流。
  - 维护内存状态，将更新推送到 Redis 并通过 WebSocket 广播给客户端。
- **缓存层**: Redis 按版本和场景存储最新的有效负载；包括 TTL 元数据和最后更新时间戳。
- **持久性**: 可选的本地文件存储（JSON 快照），用于在缓存不可用时进行热重启。

### 4.2 前端 (HTML/CSS/JavaScript)
- 由 Python 服务器呈现的静态 HTML 外壳；资产由模块化 JS（ES 模块）和 CSS（Tailwind 或自定义实用程序类）通过轻量级构建步骤（例如 Vite 或 Parcel）编译生成静态文件。
- **轮播引擎**: Vanilla JS 模块，控制场景旋转、停留计时器、会话调度以及数据过时时的故障安全冻结。
- **数据层**: 通过 REST 获取初始快照，订阅 WebSocket 以获取实时更新，并合并到状态存储中（简单的 `EventTarget` 或最小存储模式）。
- **场景**: 使用 DOM 操作（无重型框架）的每个场景的模板驱动 HTML 组件。通过脚本嵌入的轻量级图表库（TradingView Lightweight Charts 或 Apache ECharts）。
- **跑马灯和行情自动收录器**: 用于滚动行情自动收录器的 CSS 动画；响应式缩放至 4K。
- **离线处理**: Service worker 或 JS 轮询以检测断开连接，并显示带有过时指示器的缓存数据。

### 4.3 部署和基础设施
- 容器化的 Python 服务（FastAPI + 工作程序），与依赖项打包（`windpy` 可选依赖项组、`requests`、`aiohttp`、`redis`、`apscheduler`）。
- Redis 通过 Docker 容器或托管服务与之一同部署。
- Nginx（可选）作为 TLS 终止和静态缓存的反向代理。
- 信息亭设备运行指向服务 URL 的 Chromium；systemd 服务确保浏览器自动启动。

## 5. 数据流
1. 调度程序触发提供程序获取（例如 `fetch_indices`）。
2. 提供程序查询主 API（Wind 或开放）并接收数据有效负载。
3. 规范化器将字段映射到规范模式，添加版本元数据，并写入 Redis。
4. API 网关公开从 Redis 读取的 `/data/latest` 端点；观察者订阅 `/ws/stream` 以获取推送更新。
5. 前端加载初始 HTML，获取最新数据，并开始轮播。WebSocket 更新刷新 DOM，无需完全重新加载。
6. 如果提供程序获取失败，回退逻辑会尝试辅助源；如果重复失败，则设置过时标志并将其呈现给前端。

## 6. 数据提供程序
### 6.1 Wind 版
- 使用 `WindPy` 同步 API 获取 `wsq`、`wsi`、`wsd`、宏观日历端点。
- Python 服务管理 Wind 会话生命周期（`w.start()`、心跳、失败时重新连接）。
- 数据映射层将 Wind 代码（例如 `SPX.GI`）转换为友好的 ID。

### 6.2 开放版
- 使用纯 HTTP API 的开源数据栈：
  - Stooq (`https://stooq.com/q/l/`) 提供全球指数、主要美股和商品（CL/GC/SI/HG/NG 等）收盘快照；当前实现采用批量 CSV 下载 + 15 秒内存缓存，避免对同一符号重复拉取造成的 10+ 秒延迟。
  - ExchangeRate-API (`https://open.er-api.com/v6/latest/USD`) 提供公开的 FX 汇率，计算 USD/CNY、EUR/USD、USD/JPY 等交叉。
  - FRED (`https://fred.stlouisfed.org/graph/fredgraph.csv`) 暴露的免费时间序列用于利率：例如 `DGS10`/`DGS2`（美债 10Y/2Y）、`SOFR`、`EFFR` 与 `IUDSOIA`（SONIA）。接口一次性请求最近 40 天 CSV，提取最新值与前一日差值。
  - 宏观日历：优先使用 ForexFactory (`https://nfs.faireconomy.media/ff_calendar_thisweek.json`)，同时引入 TradingEconomics guest API (`https://api.tradingeconomics.com/calendar?c=guest:guest&format=json`) 作为备用源，二者均采用本地缓存（默认 15 分钟）避免频繁请求和 429 错误。
- 内置重试与指数退避，超时 10 秒。若请求失败或返回 `N/D`，自动回退 Mock 数据并记录日志。
- 可以通过 Redis（`REDIS_ENABLED`、`SNAPSHOT_CACHE_TTL`）缓存开放数据，进一步减少对公共 API 的压力。

## 7. 配置和机密
- `config.yaml` 或环境变量指定版本模式、刷新间隔、会话计划、API 密钥。
- 机密通过环境变量或机密管理器存储（用于 Wind 凭据、AlphaVantage 等 API 密钥）。
- 在启动时加载配置；通过管理端点可选地动态重新加载。

## 8. 非功能性需求
- **性能**: 后端应处理快照 API 的 <500 毫秒响应时间；WebSocket 广播在收到更新后 1 秒内完成。
- **可靠性**: 所有外部连接的自动重新连接和指数退避。对提取、流和 API 服务进行健康检查。
- **可伸缩性**: 设计为单个信息亭使用，但可通过运行共享 Redis 的多个 Python 工作程序水平扩展。
- **安全性**: HTTPS 终止；限制管理端点；确保 CORS 仅限于信息亭来源；清理 RSS/新闻内容。
- **可维护性**: 清晰分离提供程序模块；围绕数据转换的单元测试；使用结构化 JSON（例如 `structlog`）进行日志记录。

## 9. 数据存储和模式
- Redis 键：`wallboard:{edition}:{scene}` 存储 JSON 有效负载；按场景设置 TTL。
- 快照文件（可选）作为 `snapshots/{edition}-{timestamp}.json` 本地存储。
- 在共享的 Python 数据类（`pydantic` 模型）中定义的模式，用于验证。

## 10. 监控和可观察性
- 从 FastAPI 导出的 Prometheus 指标（请求延迟、错误计数）。
- 自定义指标：每个指标的数据新鲜度年龄、WebSocket 客户端连接、提供程序失败计数。
- SLA 违规的警报阈值（例如，外汇数据超过 30 秒）。
- 通过 ELK 或 Loki 堆栈进行日志聚合。

## 11. 部署管道
- CI/CD 管道运行测试、构建静态资产、对 Python (ruff) 和 JS (eslint) 进行 linting、构建 Docker 镜像。
- Wind 和开放版的单独构建目标（Wind 构建包括 `windpy` 依赖项，开放构建排除）。
- 带有迁移脚本（如果模式更改）和文档更新的版本化版本。

## 12. 操作手册（摘要）
1. **启动**: 启动 Redis -> 启动 Python 服务 -> 验证健康端点 -> 启动信息亭浏览器。
2. **版本切换**: 更新环境变量 `DATA_MODE`，重新启动 Python 服务，验证提供程序连接性。
3. **事件处理**: 检查提供程序失败的日志，确认已触发回退，如果数据差距 > SLA，则通知利益相关者。
4. **更新**: 拉取最新的容器，运行迁移（如果有），在维护窗口期间重新启动服务。

## 13. 未来增强
- 可选的管理仪表板，用于实时监控和手动覆盖。
- 与消息队列（例如 Kafka）集成，以扩展到多个墙板。
- 使用社区来源的数据集（例如 GitHub 数据转储）扩展开放版，以获取行业权重。
- 考虑为浏览器有限的环境服务器端渲染回退 PNG 幻灯片。
