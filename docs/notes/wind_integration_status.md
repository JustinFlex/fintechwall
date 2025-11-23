# Wind 集成现状与待确认事项（持续更新）

目的：记录当前 Wind 集成的进展、坑点，以及需要在 Wind 环境验证或补充的内容，便于后续接手者继续。

## 当前实现状态
- 后端 `WindProvider`：
  - 支持 WSQ，若返回全 0/空则自动 fallback 到 WSS（静态快照），统一映射为 `last/change/change_pct/open/high/low/prev_close/volume/amount/name/sector`。
  - 覆盖资产组：A/全球指数、外汇、政策利率+中美国债收益率、商品期货；商品附带 sector。
  - `/data/latest` 返回：`indices/a_shares/fx/rates/commodities/us_stocks/calendar/heatmap/summary`，并含 `data_mode`。
- `OpenProvider` 已实现：使用 Stooq HTTP 接口抓取全球指数、美股、商品；使用 ExchangeRate-API 拉取 FX；（2025-11 更新）接入 FRED（`DGS10`/`DGS2`/`SOFR`/`EFFR`/`IUDSOIA`）利率与 ForexFactory 宏观日历（带 TradingEconomics 备用源 + 15 min 缓存），数据更新仍支持 Mock 回退。
- 默认 `DATA_MODE=mock`，Wind/Open 版本通过环境变量切换。Redis 缓存可通过 `REDIS_ENABLED/SNAPSHOT_CACHE_TTL` 打开。
- 前端：`wallboard.html` 已用 `/data/latest` 渲染热力图、日历，新闻条优先用接口数据；商品显示 sector；存在的 UI 尚未完全迁移（新闻内容等可继续强化）。
- 测试：`tests/backend/test_data_latest.py` 覆盖接口基本可用性。

## 已知坑点
- WSQ 调多字段时部分资产会返回全 0（权限/闭市/字段不支持）；使用单字段 `rt_pct_chg` 成功率更高，必要时用 WSS 取价/涨跌幅。
- 商品期货：实测 `RB.SHF/TA.CZC/J.DCE/CL.NYM/GC.CMX`，WSQ `rt_pct_chg` 有值；WSS `close/pct_chg` 有值但部分为 NaN。
- 部分海外/利率代码可能因权限或闭市返回 0，需要在 Wind 终端确认可用代码。
- 依赖安装在国内网络可能超时（pydantic-settings 等），需配置镜像或预装依赖。

## 待 Wind 环境验证（建议取最简字段）
在可用 WindPy 的机器上逐组测试，记录返回值，更新代码表/映射：
1) 指数：`w.wsq("000001.SH,SPX.GI,IXIC.GI,HSI.HI", "rt_pct_chg")`
2) 外汇：`w.wsq("USDCNH.FX,USDX.FX,EURUSD.FX,USDJPY.FX", "rt_pct_chg")`
3) 利率/国债：`w.wsq("LPR1Y.IR,TB10Y.WI,UST10Y.GBM", "rt_pct_chg")`
4) 商品：已测 `RB.SHF,TA.CZC,J.DCE,CL.NYM,GC.CMX` 用 `rt_pct_chg` 正常，可补充其他品种。

如某代码 WSQ 仍为 0/NaN，用 `w.wss(codes, "close,pct_chg,volume,pre_close")` 对照；挑选有值的代码替换 `WindProvider` 常量，并在 `docs/api_specs/wind/*.csv` 记录。

## 需更新/校对的文件
- 代码表与映射：`backend/app/providers/wind.py` 常量和 `COMMODITY_SECTOR`；必要时增补 `docs/api_specs/wind/*.csv`（codes→names/sectors）。
- 网络/依赖：如在内网/国内镜像环境，先装好依赖再启动 uvicorn。

## 操作提示（PowerShell 启动示例）
- 设置 Wind 模式并启动后端：
  ```powershell
  cd .\backend
  $env:DATA_MODE = 'wind'
  uv run uvicorn app.main:app --reload
  ```
- 校验接口：
  ```powershell
  curl http://localhost:8000/data/latest
  ```
- 观察 `indices/fx/rates/commodities/heatmap` 是否有非 0/非空数据。记录异常代码后按上方“待验证”步骤分组测试，再反馈更新。
