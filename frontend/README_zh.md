# Wind 市场信息墙前端

用于信息墙的 HTML/CSS/JavaScript 信息亭客户端。布局遵循设计文档中描述的三列加跑马灯网格，并针对 16:9 4K 显示器进行了优化。

## 开发
- 入口文件: `src/index.html`
- 样式: `src/styles/main.css`
- 行为: `src/scripts/main.js`
- 管理控制台: `src/admin/index.html`，用于配置数据源和刷新覆盖。

要在本地预览，请通过静态服务器（例如 `python -m http.server`）提供 `src/` 目录的服务，并在控制台中将 `window.__WALLBOARD_API__` 设置为后端 URL（如果不同于 `http://localhost:8000`）。