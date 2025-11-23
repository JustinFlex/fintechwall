# Docker Deployment

该目录提供一键式 Docker Compose 套件，适合在没有 Wind 环境、仅依赖开放数据的场合无人值守运行。

## Quickstart – 开放数据版本

```bash
cd deployment/docker
cp backend.env.example backend.env
sed -i 's/DATA_MODE=.*/DATA_MODE=open/' backend.env
docker compose up -d --build

# 健康检查
curl http://localhost:8000/health/ready
curl http://localhost:8000/data/latest | jq '.data_mode'
```

- 前端：`http://<host>:4173/rolling-screen.html`
- 后端：`http://<host>:8000`

所有容器均设置 `restart: unless-stopped`，主机重启后会自动恢复。

## Services
- `backend`: FastAPI 应用，默认 8000 端口，读取 `backend.env`（DATA_MODE=open）。
- `frontend`: Nginx 静态站点，映射到宿主 4173 端口。
- `redis`: Redis 7，用于快照缓存，降低对外部 API 的压力。

## Customisation
- `backend.env`：可调整 Redis 地址、缓存 TTL、`DATA_MODE`、代理设置等。
- 需要覆盖 `config/defaults/*.yaml` 时，可通过 `docker-compose.yaml` 中的 `volumes` 挂载（示例：`./../../config/defaults/refresh_intervals.yaml:/app/config/refresh_intervals.yaml`）。
- 如果要在远程浏览器上访问而后端和前端不在同一主机，可在 `frontend/src/rolling-screen.html` 顶部注入 `window.__WALLBOARD_API__`（参见 `docs/ops_playbook_open_zh.md`）。

## Production Notes
- 默认镜像直接复制 `frontend/src`，若需要压缩/混淆可改造为多阶段构建。
- 若对 `/config` 等调试接口开放在公网，请加上反向代理身份认证或网络 ACL。
- 使用 `docker compose logs -f backend` 查看开放数据拉取情况，重点关注 ForexFactory 与 TradingEconomics 日志。
