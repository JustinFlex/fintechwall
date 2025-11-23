# Wind 市场信息墙前端

用于信息墙的 HTML/CSS/JavaScript 信息亭客户端。布局遵循设计文档中描述的三列加跑马灯网格，并针对 16:9 4K 显示器进行了优化。

## 快速预览（最小可运行页面）
- 推荐页面：`src/wallboard.html`（现代风格），或 `src/index.html`（基础占位场景）。
- 迁移自 `FrontendDesign` 的自动轮播版：`src/rolling-screen.html`（多场景大屏）。
- 本地起一个静态服务器（示例）：
  ```bash
  cd frontend
  python -m http.server 8001 -d src
  # 浏览器打开 http://localhost:8001/wallboard.html
  ```
- 如果需要指向非默认后端，可在控制台设置 `window.__WALLBOARD_API__ = "http://localhost:8000"`。
- `rolling-screen.html` 默认轮询 `/data/latest`，顶部显示数据模式与更新时间，并内置倒计时、新闻条等组件，是验收开放数据栈的首选入口。

## 结构
- 入口文件: `src/wallboard.html`（现代版）/ `src/index.html`（基础版）/ `src/rolling-screen.html`（设计稿迁移）
- 样式: `src/styles/main.css`, `src/styles/wallboard-modern.css`, `src/styles/a-shares.css`, `src/styles/rolling-screen.css` 等
- 行为: `src/scripts/main.js`, `src/scripts/wallboard.js`, `src/scripts/a-shares.js`, `src/scripts/rolling-screen.js`
- 管理控制台: `src/admin/index.html`，用于配置数据源和刷新覆盖。

## 与后端的协同
- 所有实时页面通过 `scripts/dataClient.js` 访问 `/data/latest`，失败时会在 UI 顶部显示“离线”状态。
- `rolling-screen.js` 中的 `SCENES` 描述了七个轮播页面，新增场景或字段时，请保持与后端快照结构一致。
- 如果部署在 kiosk / VM，可配合 `deployment/launcher/start_open_wallboard.sh` 一键脚本，让静态服务器监听 `4173` 端口，浏览器直接打开 `http://localhost:4173/rolling-screen.html`。
