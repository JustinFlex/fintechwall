# 数据 API 需求说明（按大屏内容拆分）

> 目的：本文件只描述“我们需要什么类型的数据接口”，而 **不绑定具体厂商**（Wind、AkShare、券商、自建等）。  
> 你可以据此去寻找或整理对应的数据源与 API 文档，并统一放在例如 `docs/api_specs/` 目录中，后端只需要对接到这些“逻辑 API 类型”即可。

---

## 1. 总览：页面 / 场景 与数据类型对应关系

### 1.1 7 个页面（最初中文大屏设计）

- 页面一：全球指数概览  
  - `GLOBAL_INDICES_SNAPSHOT` – 全球主要股指快照  
  - `FX_SNAPSHOT` – 主要外汇对快照  
  - `COMMODITY_KEY_FUTURES_SNAPSHOT` – 关键大宗商品期货快照  
  - `RATES_KEY_TENORS_SNAPSHOT` – 关键利率/国债收益率点位  
  - `CRYPTO_LARGE_CAP_SNAPSHOT`（可选） – BTC/ETH 等大市值币种快照  
  - `EXCHANGE_STATUS` – 主要交易所开闭市状态  

- 页面二：A 股市场概览  
  - `A_SHARES_INDEX_SNAPSHOT` – 上证/深证/沪深 300/中证 1000 等指数  
  - `A_SHARES_SECTOR_HEATMAP` – 行业/概念板块涨跌热力图  
  - `A_SHARES_MARKET_BREADTH` – 涨跌家数、成交额、换手率等整体情绪指标  
  - `ETF_SNAPSHOT_CN` – 主要股票类 ETF 快照  

- 页面三：A 股短线资金聚焦  
  - `A_SHARES_TOP_MOVERS_INTRADAY` – 涨幅榜/跌幅榜/成交额榜  
  - `A_SHARES_LIMIT_UP_BOARD` – 连板股与涨停股列表  
  - `A_SHARES_LHB` – 龙虎榜数据（机构/席位买卖）  
  - `A_SHARES_SENTIMENT_SCORE`（可选） – 新闻/舆情/北向资金等综合情绪分  

- 页面四：债券市场全景  
  - `YIELD_CURVE_CN` – 中国国债收益率曲线  
  - `YIELD_CURVE_US` – 美国国债收益率曲线  
  - `CREDIT_CURVE_CN_AAA` – 中国 AAA 信用债收益率曲线  
  - `RATES_POLICY_BENCHMARKS` – LPR、政策利率、SHIBOR 等关键利率  

- 页面五：大宗商品市场  
  - `COMMODITY_KEY_FUTURES_SNAPSHOT` – 主要商品主力合约（螺纹钢、沪铜、原油等）  
  - `COMMODITY_SECTOR_HEATMAP` – 不同品种/板块的涨跌表现  
  - `COMMODITY_NEWS_PULSE`（可选） – 商品市场相关要闻/快讯  

- 页面六：另类与数字资产  
  - `CRYPTO_LARGE_CAP_SNAPSHOT` – BTC/ETH 等现货行情  
  - `CRYPTO_DERIVATIVES_METRICS` – 资金费率、未平仓合约、隐含波动率等  
  - `ONCHAIN_ACTIVITY_METRICS`（可选） – Gas 费、链上活跃地址、TVL 等  
  - `ALT_FUNDS_PE_VC_SUMMARY`（可选） – PE/VC 等另类资产交易概要（如仅做静态说明，可用手动数据）  

- 页面七：市场大事倒计时  
  - `MACRO_EVENT_CALENDAR` – 未来一周/一月重要宏观事件与经济数据  
  - `CENTRAL_BANK_DECISION_CALENDAR` – 主要央行议息与决策日程  
  - `EVENT_COUNTDOWN_CONFIG` – 手动配置的关键事件（如“某只 IPO 上市日”）  
  - `MACRO_NEWS_HEADLINES`（可选） – 作为补充的宏观要闻标题  

### 1.2 5 个场景（FintechWallProjects PRD 中的 A–E）

大致可以映射为：

- 场景 A – 全球概览  
  - 对应 页面一 + 部分 页面四/六 的简化快照：  
  - `GLOBAL_INDICES_SNAPSHOT`、`FX_SNAPSHOT`、`COMMODITY_KEY_FUTURES_SNAPSHOT`、`RATES_KEY_TENORS_SNAPSHOT`、`CRYPTO_LARGE_CAP_SNAPSHOT`、`EXCHANGE_STATUS`

- 场景 B – 股票热图  
  - 以 A 股/全球股票为主：  
  - `A_SHARES_SECTOR_HEATMAP`、`A_SHARES_TOP_MOVERS_INTRADAY`、`VOLATILITY_INDICES_GLOBAL`（如 VIX、VXN）、`A_SHARES_MARKET_BREADTH`

- 场景 C – 宏观与利率  
  - 主要使用：  
  - `YIELD_CURVE_CN`、`YIELD_CURVE_US`、`CREDIT_CURVE_CN_AAA`、`RATES_POLICY_BENCHMARKS`、`MACRO_EVENT_CALENDAR`、`CENTRAL_BANK_DECISION_CALENDAR`

- 场景 D – 加密货币深度  
  - 主要使用：  
  - `CRYPTO_LARGE_CAP_SNAPSHOT`、`CRYPTO_DERIVATIVES_METRICS`、`STABLECOIN_FLOWS`、`ONCHAIN_ACTIVITY_METRICS`

- 场景 E – 新闻横幅  
  - 主要使用：  
  - `MARKET_NEWS_HEADLINES`、`MACRO_NEWS_HEADLINES`、`RISK_SIGNALS_SUMMARY`

---

## 2. 数据 API 类型定义（逻辑接口）

### 2.1 全球 &指数 / 外汇 / 商品 / 利率

#### GLOBAL_INDICES_SNAPSHOT – 全球主要股指快照

- 用途：页面一、场景 A 的核心卡片数据。  
- 更新频率：交易时段内最好 10–30 秒一跳；最慢不超过 60 秒。  
- 最小字段：
  - `symbol`（例如 `SPX`, `NDX`, `000001.SH`, `HSI`）
  - `name`（指数名称）
  - `last`（最新点位）
  - `change`（涨跌额）
  - `pct_change`（涨跌幅，%）
  - `open`, `high`, `low`, `prev_close`（可选）
  - `volume`（可选）
  - `market_status`（`open` / `closed` / `pre` / `post`）
  - `currency`
  - `last_update`（时间戳）

#### FX_SNAPSHOT – 主要外汇对快照

- 用途：页面一、场景 A 中的 FX 行。  
- 最小字段：
  - `pair`（如 `EURUSD`, `USDJPY`, `USDCNH`）
  - `bid`, `ask` 或 `mid`
  - `pct_change_24h`
  - `last_update`

#### COMMODITY_KEY_FUTURES_SNAPSHOT – 关键大宗商品期货

- 用途：页面一、五，场景 A。  
- 最小字段：
  - `symbol`（期货代码）
  - `name`
  - `last`
  - `pct_change`
  - `volume`（可选）
  - `open_interest`（可选）
  - `last_update`

#### RATES_KEY_TENORS_SNAPSHOT – 关键利率/国债收益率点位

- 用途：页面一、四，场景 A/C 顶部概览。  
- 内容示例：中美 2Y/5Y/10Y 国债收益率，3M/1Y 政策利率等。  
- 最小字段：
  - `series_id`（例如 `US10Y`, `CN10Y`, `FF_TARGET`）
  - `name`
  - `value`（收益率或利率，%）
  - `change_bp`（较前一交易日变动，bp，可选）
  - `last_update`

#### EXCHANGE_STATUS – 交易所开闭市状态

- 用途：场景 A 的“市场状态”指示器。  
- 最小字段：
  - `exchange_code`（如 `NYSE`, `NASDAQ`, `SSE`, `SZSE`, `HKEX`）
  - `status`（`open` / `closed` / `holiday` / `auction` 等）
  - `next_open` / `next_close`（可选）
  - `last_update`

---

### 2.2 A 股指数、板块与市场情绪

#### A_SHARES_INDEX_SNAPSHOT – 核心指数快照

- 用途：页面二核心指标。  
- 覆盖：`000001.SH`, `399001.SZ`, `000300.SH`, `000852.SH` 等。  
- 字段同 `GLOBAL_INDICES_SNAPSHOT`，可视为其子集。

#### A_SHARES_SECTOR_HEATMAP – 行业/概念板块热力图

- 用途：页面二/场景 B 的热力图。  
- 最小字段：
  - `sector_id`（板块代码）
  - `sector_name`
  - `pct_change`（板块整体涨跌幅）
  - `turnover`（成交额，总额）
  - `advancers` / `decliners`（板块内涨跌家数，可选）
  - `last_update`

#### A_SHARES_MARKET_BREADTH – 市场广度/情绪指标

- 用途：页面二/场景 B 的“情绪晴雨表”。  
- 最小字段：
  - `advancers`（上涨家数）
  - `decliners`（下跌家数）
  - `limit_up_count` / `limit_down_count`
  - `total_turnover`（全市场成交额）
  - `northbound_net_flow`（北向资金净流入，可选）
  - `vix_cn`（如中国波指，可选）
  - `last_update`

#### ETF_SNAPSHOT_CN – A 股 ETF 快照

- 用途：页面二与资金流相关卡片。  
- 最小字段：
  - `symbol`
  - `name`
  - `pct_change`
  - `turnover`
  - `last_update`

#### A_SHARES_TOP_MOVERS_INTRADAY – 涨跌/成交榜

- 用途：页面三的短线资金榜单。  
- 最小字段：
  - `symbol`
  - `name`
  - `pct_change`
  - `turnover`
  - `turnover_rate`（换手率，可选）
  - `volume_ratio`（量比，可选）
  - `last_update`

#### A_SHARES_LIMIT_UP_BOARD – 涨停/连板股

- 用途：页面三“连板信号榜”。  
- 最小字段：
  - `symbol`
  - `name`
  - `limit_up_days`（连板天数）
  - `turnover_rate`
  - `pct_change`
  - `first_limit_time`（首次封板时间，可选）
  - `last_update`

#### A_SHARES_LHB – 龙虎榜

- 用途：页面三“机构席位龙虎榜”。  
- 最小字段（可按股票聚合，也可按席位聚合）：
  - `symbol`
  - `name`
  - `side`（`buy`/`sell`/`net`）
  - `broker` / `seat_name`
  - `amount`（金额）
  - `trade_date`

#### A_SHARES_SENTIMENT_SCORE（可选）

- 用途：页面二/三的综合情绪分，一般为自建指标。  
- 最小字段：
  - `score`（0–100）
  - `description`（自然语言解释）
  - `last_update`

---

### 2.3 债券与宏观利率

#### YIELD_CURVE_CN – 中国国债收益率曲线

- 用途：页面四/场景 C 的收益率曲线图。  
- 最小字段：
  - `tenor`（如 `1Y`, `3Y`, `5Y`, `10Y`）
  - `yield`（当前收益率，%）
  - `yield_prev`（前一时点/周收益率，用于对比，可选）
  - `as_of_date`（日期）

#### YIELD_CURVE_US – 美国国债收益率曲线

- 字段同 `YIELD_CURVE_CN`，仅国家不同。

#### CREDIT_CURVE_CN_AAA – 中国 AAA 信用债曲线

- 用途：页面四中“利差/信用风险”相关图表。  
- 最小字段：
  - `tenor`
  - `yield`
  - `spread_vs_govt`（相对国债利差，可选）
  - `as_of_date`

#### RATES_POLICY_BENCHMARKS – 政策利率与短端利率

- 用途：页面四/场景 C 小组件（LPR、MLF、SHIBOR 等）。  
- 最小字段：
  - `rate_id`（如 `LPR_1Y`, `LPR_5Y`, `SHIBOR_O/N`）
  - `name`
  - `value`
  - `change_bp`
  - `last_update`

#### CENTRAL_BANK_EXPECTATIONS（可选）

- 用途：联邦基金利率路径、加息概率等可视化。  
- 形式可为：按会议日期列出市场隐含利率或概率分布。

---

### 2.4 宏观事件与新闻

#### MACRO_EVENT_CALENDAR – 宏观/经济数据日历

- 用途：页面七/场景 C 的财经日历与倒计时。  
- 最小字段：
  - `event_id`
  - `title`（事件名称，如“美国非农就业”）
  - `country` / `region`
  - `datetime`（发布时间，含时区）
  - `importance`（1–3 或 `low/mid/high`）
  - `actual` / `consensus` / `previous`（可选）

#### CENTRAL_BANK_DECISION_CALENDAR – 央行议息日程

- 可视为 `MACRO_EVENT_CALENDAR` 子集，但字段中应包含：
  - `central_bank`（如 `Fed`, `ECB`, `PBoC`）
  - `decision_type`（`rate_decision` 等）

#### EVENT_COUNTDOWN_CONFIG – 手动关键事件配置

- 用途：页面七的“市场大事倒计时”（自定义事件）。  
- 可以是后台配置或本地文件，字段：
  - `event_id`
  - `title`
  - `datetime`
  - `description`（可选）

#### MARKET_NEWS_HEADLINES / MACRO_NEWS_HEADLINES

- 用途：全局跑马灯/场景 E 新闻条。  
- 最小字段：
  - `headline_id`
  - `title`
  - `source`
  - `published_at`
  - `url`（可选，用于后台调试）

#### RISK_SIGNALS_SUMMARY（可选）

- 用途：场景 E 的“风险高亮”（如 VIX>阈值、曲线倒挂等）。  
- 建议由后端在聚合层结合多种数据计算，而非直接来自单一外部 API。

---

### 2.5 加密货币与链上数据

#### CRYPTO_LARGE_CAP_SNAPSHOT – 主要加密货币现货快照

- 用途：页面六/场景 D 的现货行情。  
- 最小字段：
  - `symbol`（如 `BTCUSDT`, `ETHUSDT`）
  - `price`
  - `pct_change_24h`
  - `volume_24h`
  - `market_cap`（可选）
  - `last_update`

#### CRYPTO_DERIVATIVES_METRICS – 衍生品与资金费率

- 用途：场景 D 的资金费率、未平仓等。  
- 最小字段：
  - `symbol`
  - `funding_rate`
  - `open_interest`
  - `implied_vol_30d`（可选）
  - `volume_24h`
  - `last_update`

#### STABLECOIN_FLOWS（可选）

- 用途：稳定币资金流向指标。  
- 可以是按链或按交易所：
  - `asset`（`USDT`, `USDC` 等）
  - `net_flow_24h`
  - `net_flow_7d`
  - `last_update`

#### ONCHAIN_ACTIVITY_METRICS（可选）

- 用途：页面六/场景 D 中的链上活动概览。  
- 最小字段：
  - `network`（`Ethereum`, `Bitcoin` 等）
  - `active_addresses`
  - `tx_count_24h`
  - `avg_fee` / `gas_price`
  - `tvl`（如来自 DeFi 聚合）
  - `last_update`

#### ALT_FUNDS_PE_VC_SUMMARY（可选）

- 如果需要展示 PE/VC 等另类资产，只要提供按时间聚合的：
  - `date`
  - `deal_count`
  - `total_amount`
  - `top_themes`（可选，字符串）

---

## 3. 后续对接建议

1. **你这边的工作**  
   - 按上述“逻辑 API 类型”去寻找/筛选实际数据源（Wind、AkShare、券商 API、自建爬虫等）。  
   - 把每个逻辑类型映射到一份清晰的 API 说明文档，并统一放在例如 `FintechWallProjects/docs/api_specs/` 目录下（可以按厂商分子文件夹）。  

2. **后端这边的工作**  
   - 为每一种逻辑类型定义一个 Python 抽象接口（例如 `fetch_global_indices_snapshot()`），返回统一 schema。  
   - 每接入一个具体数据源，就实现一套 Provider，把外部 API 的字段映射到上述统一 schema。  

3. **前端这边的工作**  
   - 只依赖统一的后端 JSON 结构，不直接关心是 Wind 还是开源 API。  
   - 所有页面/场景从同一个 `/data/latest` 或类似端点获取上述数据块并渲染。  

这样一来，只要你把可靠、专业的 API 文档整理好并放入指定目录，我就可以直接根据这份 `data-api-requirements_zh.md` 和你的 API 文档，帮你实现对应的 Provider 与后端对接逻辑。 

