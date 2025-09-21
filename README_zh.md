# Wind 市场信息墙项目

此目录托管项目文档（`docs/`）中描述的 Wind 市场信息墙的实现。

结构：
- `backend/`: Python 服务（FastAPI 网关、数据提取、提供程序）。
- `frontend/`: HTML/CSS/JavaScript 信息亭客户端源文件。
- `config/`: 版本配置模板、会话计划、刷新间隔。
- `deployment/`: Docker、systemd、信息亭脚本。
- `infra/`: 基础设施即代码、监控清单。
- `tests/`: 共享测试资产、集成装置。
- `docs/`: 开发过程中生成的项目特定设计说明。

有关活动待办事项，请参阅存储库根目录中的 `todo.md`。