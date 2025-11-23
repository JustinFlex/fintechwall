# 一键启动脚本（开放数据版）

`start_open_wallboard.sh` 让非技术用户可以“点一下就看大屏”：

1. **前置要求**
   - Linux/WSL/macOS 终端。
   - 已安装 Python 3.11+ 与 [`uv`](https://docs.astral.sh/uv/)（可用 `pipx install uv` 或 `pip install --user --break-system-packages uv`）。
2. **执行**
   ```bash
   cd FintechWallProjects/FintechWallProjects
   ./deployment/launcher/start_open_wallboard.sh
   ```
3. 脚本会自动：
   - 复制 `config/defaults/backend.env` 并强制 `DATA_MODE=open`；
   - 如果 `backend/.venv` 不存在，运行 `uv sync` 安装依赖；
   - 启动 FastAPI 后端（端口 8000）与前端静态服务器（端口 4173）；
   - 尝试自动打开浏览器访问 `http://localhost:4173/rolling-screen.html`；
   - 在 `logs/backend.log`、`logs/frontend.log` 中记录输出。
4. **退出**
   - 按 `Ctrl+C` 即可一次性停止前后端。

> 注：该脚本默认使用开放数据源（Stooq/FRED/ForexFactory/TradingEconomics），如需切换到 Wind，请手动修改 `backend/.env` 或直接运行其他部署方案。
