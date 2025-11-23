# 开放数据版无人值守部署手册

本手册面向无需 Wind 环境、只依赖开源免费数据源的部署场景，提供两种**无人值守**安装方案（Docker Compose 与 systemd）以及运行监控/排障指引。

---

## 1. 前置准备

- 目标主机：Ubuntu 22.04+/Debian 12+/CentOS Stream 等任意支持 systemd 与 Docker 的 Linux 发行版。
- 网络：可访问 Stooq、FRED、ForexFactory、TradingEconomics（HTTP/HTTPS 直连）。
- 端口：默认开放 `8000`（后端）与 `4173`（前端）。
- 必备软件：
  - Docker 24+ 与 Docker Compose v2（方案 A）
  - Python 3.11+、`uv`、systemd（方案 B）

确保 `config/defaults/backend.env` 被复制为最终 `.env`，并调整为：

```ini
DATA_MODE=open
REDIS_ENABLED=true  # 推荐启用 redis:7 容器或本地 Redis 以降低延迟
REDIS_URL=redis://redis:6379/0
SNAPSHOT_CACHE_TTL=15
```

---

## 2. 一键脚本（本地快速验收）

适合想“点一下就看”的非技术用户，脚本位于 `deployment/launcher/start_open_wallboard.sh`：

1. 安装 `uv`（若尚未安装）：`pipx install uv`。
2. 进入仓库根目录运行：
   ```bash
   ./deployment/launcher/start_open_wallboard.sh
   ```
3. 脚本会自动复制 `.env`、将 `DATA_MODE=open`、安装依赖、启动后端/前端，并尝试打开浏览器访问 `http://localhost:4173/rolling-screen.html`。
4. 需要停止时在终端按 `Ctrl+C`。

若要改端口或切换数据源，可手动编辑 `backend/.env` 后再重新运行脚本。

---

## 3. 方案 A：Docker Compose（推荐给 kiosk/PoC）

1. **下载代码并构建**
   ```bash
   git clone https://example.com/FintechWallProjects.git /opt/fintech-wallboard
   cd /opt/fintech-wallboard/FintechWallProjects/deployment/docker
   cp backend.env.example backend.env
   sed -i 's/DATA_MODE=.*/DATA_MODE=open/' backend.env
   docker compose up -d --build
   ```

2. **健康检查**
   ```bash
   curl http://localhost:8000/health/ready
   curl http://localhost:8000/data/latest | jq '.data_mode'
   # 期待输出 "open"
   ```

3. **前端访问**
   - 浏览器访问 `http://<主机>:4173/rolling-screen.html`。
   - 需要墙面信息亭时，可把浏览器设置为 kiosk 模式并开启全屏自动刷新。

4. **自动重启**
   - `docker compose` 服务默认 `restart: unless-stopped`，主机重启后将自动拉起。

---

## 4. 方案 B：systemd + uv（无容器环境）

1. **安装依赖**
   ```bash
   sudo apt update && sudo apt install -y python3.11 python3.11-venv git
   pipx install uv  # 或 pip install uv --break-system-packages
   ```

2. **克隆仓库并拉取依赖**
   ```bash
   sudo git clone https://example.com/FintechWallProjects.git /opt/fintech-wallboard
   cd /opt/fintech-wallboard/FintechWallProjects/backend
   uv sync
   cp ../config/defaults/backend.env .env
   sed -i 's/DATA_MODE=.*/DATA_MODE=open/' .env
   ```

3. **创建运行用户（可选）**
   ```bash
   sudo useradd --system --home /opt/fintech-wallboard --shell /usr/sbin/nologin wallboard
   sudo chown -R wallboard:wallboard /opt/fintech-wallboard
   ```

4. **安装 systemd 单元**
   ```bash
   cd /opt/fintech-wallboard/FintechWallProjects
   sudo cp deployment/systemd/wallboard-*.service /etc/systemd/system/
   sudoedit /etc/systemd/system/wallboard-backend.service  # 修改 WorkingDirectory/ExecStart 路径
   sudoedit /etc/systemd/system/wallboard-frontend.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now wallboard-backend.service
   sudo systemctl enable --now wallboard-frontend.service
   ```

5. **验证**
   ```bash
   systemctl status wallboard-backend
   curl http://127.0.0.1:8000/health/live
   curl http://127.0.0.1:8000/data/latest | jq '.timestamp'
   ```

---

## 5. 运行监控与告警建议

### 4.1 自动探针脚本

- 提供 `deployment/monitoring/open_data_probe.sh`，依赖 `jq` 与 `curl`。
- 该脚本会：
  1. 请求 `/health/ready`；
  2. 拉取 `/data/latest` 并校验 `data_mode=open`；
  3. 检查 `SPX.GI`（Stooq）、`UST10Y.GBM`/`SOFR.IR`（FRED）、`calendar.events[0].source`（ForexFactory/TradingEconomics）字段是否存在。
- 示例 Cron（每 5 分钟运行一次并写入 syslog）：
  ```cron
  */5 * * * * API_BASE=http://127.0.0.1:8000 /opt/fintech-wallboard/FintechWallProjects/deployment/monitoring/open_data_probe.sh \
    2>&1 | /usr/bin/logger -t wallboard-probe
  ```
- 若在 Prometheus 中集成，可通过 node_exporter textfile/blackbox exporter 调用该脚本并暴露退出码。

### 4.2 指标参考

| 指标 | 获取方式 | 阈值/处理 |
| --- | --- | --- |
| 快照延迟 | `curl /data/latest` 中 `timestamp` 与当前时间差值 | >120s 代表外部 API 失败，检查日志与网络；若仅宏观日历缺失，可等待 15 分钟缓存。 |
| API 健康 | `/health/live`、`/health/ready` | 任一失败时自动重启或告警。 |
| ForexFactory/TradingEconomics 退避 | `journalctl -u wallboard-backend -f` 内 `ForexFactory`/`TradingEconomics` 关键词 | 连续 429：确认外网连通或临时调高 `FOREXFACTORY_COOLDOWN_TTL`。 |
| Redis 状态 | `docker ps` 或 `systemctl status redis`（如自建） | 未运行会退回内存模式，监控日志 `Cache disabled`。 |

可以使用 `cron` 或 `Prometheus node_exporter + blackbox_exporter` 定期拉取 `/data/latest`，把 `timestamp` 与当前时间差作为监控项，并设置 2 分钟阈值。

---

## 6. 常见故障排查

1. **前端显示“等待数据”**
   - 检查浏览器控制台是否有 `CORS` 或 `fetch` 错误。
   - 若使用远程浏览器访问，需要在 `frontend/src/rolling-screen.html` 中加入：
     ```html
     <script>window.__WALLBOARD_API__ = "http://<backend-host>:8000";</script>
     ```

2. **ForexFactory 429**
   - 日志会提示“cooldown”。等待 15 分钟，TradingEconomics 备用源会保持日历可用。

3. **依赖缺失**
   - `systemctl status wallboard-backend` 若提示 `uv: command not found`，请以部署用户安装 `uv` 并确保 `PATH` 包含其安装目录，或把 `ExecStart` 换成 `.venv/bin/uvicorn`。

4. **端口被占用**
   - 修改 `deployment/systemd/*.service` 或 `docker-compose.yaml` 的端口映射，然后 `systemctl restart` / `docker compose up -d`。

---

## 7. 交接清单

- [ ] `DATA_MODE=open` 并能成功请求 `/data/latest`。
- [ ] `docker compose ps` 或 `systemctl status` 显示所有服务为 `running`。
- [ ] 记录部署主机 IP、端口、登录账户（如 `wallboard`）。
- [ ] `journalctl -u wallboard-backend --since "-5 min"` 无连续报错。
- [ ] 提供本手册链接给运维人员，确认对监控/故障流程知晓。

---

## 8. 本机 Dry-run 记录（2025-11-22）

在本仓库的 WSL2 环境中对 Docker / systemd 指令做了演练，确认以下事项：

1. **Docker Compose**
   - 首次执行需要安装依赖：`sudo apt-get install -y docker.io docker-compose && sudo service docker start`。
   - 由于 WSL 主机无法访问 `registry-1.docker.io`（TLS 握手在 60 秒后超时），`docker-compose up --build` 无法拉取 `python:3.11-slim`，需要在真正部署机器上配置镜像站或公司代理（例如设置 `/etc/docker/daemon.json` 指向国内镜像、或在执行命令前导出 `HTTPS_PROXY`）。
   - `deployment/docker/Dockerfile.backend` 已修复多行 `ENV/RUN` 语法，确保镜像构建在拥有 Docker Hub 访问权限的机器上可以直接通过。

2. **systemd/uv 模式**
   - `deployment/uv/run_backend.sh` / `serve_frontend.sh` 原本为 CRLF 结尾，导致 `/usr/bin/env: 'bash\r': No such file or directory`；已统一转为 LF，运行前无需额外处理。
   - 在根用户下安装 `uv`：`pip install --user --break-system-packages uv`，并在执行脚本前添加 `PATH="/root/.local/bin:$PATH"`。
   - Dry-run 命令：
     ```bash
     PATH="/root/.local/bin:$PATH" DATA_MODE=open ./deployment/uv/run_backend.sh > /tmp/wallboard_backend.log &
     ./deployment/uv/serve_frontend.sh > /tmp/wallboard_frontend.log &
     ```
   - 验证：
     ```bash
     curl -s http://127.0.0.1:8000/data/latest | jq '.data_mode'
     # 输出 "open"，payload 中可看到 Stooq / FRED / ForexFactory 场景。
     curl -s http://127.0.0.1:4173/rolling-screen.html | head
     ```
   - 运行完毕记得 `kill <uvicorn_pid>` 与 `kill <python3_http_server_pid>`，并删除 `backend/.venv`（`uv run` 临时生成）。

3. **外网连通性**
   - `curl http://127.0.0.1:8000/data/latest` 成功返回实时快照，`rates` 内含 `UST10Y.GBM`/`SOFR.IR`，`calendar.events[].source` 包含 `ForexFactory`，表明 FRED / ForexFactory / TradingEconomics 均可访问。
   - 若日后在其他机器上拉取失败，可通过直接访问 `https://stooq.com/q/l/?s=spx.us&f=sd2t2ohlcv&e=csv`、`https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10` 判断网络是否被墙。

以上记录可作为现场部署 checklist 的补充，应根据实际宿主机环境（代理、权限、文件系统差异）做进一步调整。
