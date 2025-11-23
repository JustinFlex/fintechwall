# systemd 部署模板（开放数据模式）

此目录提供了两个示例 `systemd` 单元文件，用于在裸机/VM 上以 **DATA_MODE=open** 模式无人值守地运行信息墙：

- `wallboard-backend.service` – 通过 `deployment/uv/run_backend.sh` 启动 FastAPI 后端。
- `wallboard-frontend.service` – 依赖 `python3 -m http.server` 提供前端静态资源。

## 使用步骤

1. **准备代码与依赖**
   - 克隆仓库到目标路径（例如 `/opt/fintech-wallboard`）。
   - 安装 `uv` 并在 `backend/` 目录执行 `uv sync`，确保依赖被下载到 `.venv`。
   - 复制 `config/defaults/backend.env` 至 `backend/.env`，设置 `DATA_MODE=open` 和 Redis 等参数。

2. **创建运行用户（可选但推荐）**
   ```bash
   sudo useradd --system --create-home --shell /usr/sbin/nologin wallboard
   sudo chown -R wallboard:wallboard /opt/fintech-wallboard
   ```

3. **复制并编辑服务文件**
   ```bash
   sudo cp deployment/systemd/wallboard-*.service /etc/systemd/system/
   sudoedit /etc/systemd/system/wallboard-backend.service
   sudoedit /etc/systemd/system/wallboard-frontend.service
   ```
   - 将 `WorkingDirectory`、`ExecStart` 和 `EnvironmentFile` 替换为实际路径。
   - 如果创建了 `wallboard` 用户，保持 `User=wallboard`/`Group=wallboard`。

4. **启动并设置开机自启**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now wallboard-backend.service
   sudo systemctl enable --now wallboard-frontend.service
   ```

5. **健康检查**
   - 后端：`curl http://localhost:8000/health/ready`
   - 前端：浏览器访问 `http://<host>:4173/rolling-screen.html`

更详细的无人值守安装、监控与故障排查见 `docs/ops_playbook_open_zh.md`。
