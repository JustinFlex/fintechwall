# Wind 市场信息墙项目

此目录托管项目文档（`docs/`）中描述的 Wind / 开源数据大屏实现。按照 PRD 要求，后端聚合多源行情，前端以信息亭模式轮播展示。

## 结构速览
- `backend/`：FastAPI 服务、数据提供方（Wind/Open/Mock）、缓存与健康检查。
- `frontend/`：HTML/CSS/JavaScript 信息亭客户端，包含 `wallboard.html` 与 `rolling-screen.html`。
- `config/`：环境变量模板、刷新间隔、轮播排程等配置。
- `deployment/`：Docker、systemd、启动脚本、监控探针。
- `docs/`：PRD、技术架构、运维与现状笔记。
- `tests/`：后端单测/探针。

有关路线图，请查看仓库根目录 `TODO.md`；日常验收与差距记录集中在 `docs/notes/open_mode_gaps.md`。

## 快速启动（开放数据模式）
工程提供一键脚本，方便在 WSL/VM 中拉起完整链路：

```bash
cd FintechWallProjects
./deployment/launcher/start_open_wallboard.sh
```

该脚本会执行：
1. 检查 `backend/.env`，确保 `DATA_MODE=open`；
2. 使用 `uv` 安装依赖并运行 `uvicorn app.main:app`；
3. 通过 `python -m http.server 4173 -d frontend/src` 暴露静态页面；
4. 输出日志到 `logs/backend.log` 与 `logs/frontend.log`。

浏览器打开 `http://localhost:4173/rolling-screen.html` 即可观察七个场景的轮播表现、数据更新时间、倒计时等模块。

如需手动分步启动：

```bash
# 后端
cd backend
uv sync
DATA_MODE=open uv run uvicorn app.main:app --reload

# 前端（静态服务器）
cd ../frontend
python -m http.server 4173 -d src
```

## 数据源模式
- `DATA_MODE=mock`：使用 `MockProvider`，适合脱网场景或联调。
- `DATA_MODE=open`：组合腾讯行情 + Stooq 兜底 + AlphaVantage（商品）+ 中国货币网（利率曲线）+ FRED + CoinGecko + FXStreet 事件列表。支持 `ALPHAVANTAGE_API_KEY`、`SNAPSHOT_CACHE_TTL` 等参数。
- `DATA_MODE=wind`：需具备 WindPy/WAPI 环境，详情见 `docs/notes/wind_integration_status.md`。

环境变量默认模板位于 `config/defaults/backend.env`，可通过 `deployment/launcher` 或自定义脚本拷贝。

## 运维参考
- `docs/ops_playbook_open_zh.md`：开放模式的巡检、日志、常见故障排查。
- `deployment/systemd/`：信息亭服务示例；`deployment/docker/` 给出容器化指引。
- `deployment/monitoring/open_data_probe.sh`：可在 Cron 中定时运行，检测 `/data/latest` 是否健康。

如需了解具体的数据差距与下一步优先级，请结合 `PROJECT.md`、「M5」章节及 `docs/notes/open_mode_gaps.md`。
