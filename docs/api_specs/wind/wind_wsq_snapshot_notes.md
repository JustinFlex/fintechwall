# Wind WSQ 实时订阅示例整合说明（指数 / 利率 / 外汇 / 商品期货）

你上传的若干示例文件展示了使用 `w.wsq` 一次性订阅 **指数 / 外汇 / 利率（国债收益率、政策利率、Shibor 等）/ 商品期货** 的实时快照。这里总结如何把这些原始表映射到我们在 `data-api-requirements_zh.md` 定义的“逻辑 API 类型”。

## 1. 原始调用与字段

- 指数 / 外汇 / 利率 / 收益率曲线调用示例：见 `各个api调用示例.txt`  
  `w.wsq(<长列表>, "rt_date,rt_time,rt_pre_close,rt_open,rt_high,rt_low,rt_last,rt_last_amt,rt_last_vol,rt_latest,rt_vol,rt_amt,rt_chg,rt_pct_chg,rt_mkt_vol,rt_up_total,rt_same_total,rt_down_total,rt_pe_ttm", "pricetype=3", func=DemoWSQCallback)`
- 商品期货调用示例：见 `各个api调用示例（商品期货类）.txt`  
  `w.wsq("GC.CMX,SI.CMX,HG.CMX,ALI.CMX,CL.NYM,PL.NYM,NG.NYM,TA.CZC,J.DCE,SA.CZC,S.CBT,C.CBT,W.CBT,ZE.CBT,LH.DCE,RB.SHF","rt_date,rt_time,rt_pre_close,rt_high,rt_open,rt_low,rt_last,rt_last_amt,rt_last_vol,rt_latest,rt_vol,rt_amt,rt_chg,rt_pct_chg",func=DemoWSQCallback)`

- 字段（CSV 列）：
  - 时间戳：`RT_DATE`(YYYYMMDD), `RT_TIME`(HHMMSS or HHMM)
  - 价格：`RT_PRE_CLOSE`, `RT_OPEN`, `RT_HIGH`, `RT_LOW`, `RT_LAST`（最新）, `RT_CHG`, `RT_PCT_CHG`
  - 成交：`RT_LAST_AMT`, `RT_LAST_VOL`, `RT_VOL`, `RT_AMT`, `RT_LATEST`, `RT_MKT_VOL`
  - 盘口/广度：`RT_UP_TOTAL`, `RT_SAME_TOTAL`, `RT_DOWN_TOTAL`
  - 估值：`RT_PE_TTM`
- 注意：
  - 对于利率/收益率类资产（LPR、Shibor、国债收益率、金融债收益率等），成交/估值等字段多数为 0，仅 `RT_LAST` 有意义，请在解析时按资产类型选择字段。
  - 对于商品期货，`RT_LAST`、`RT_CHG`、`RT_PCT_CHG` 有意义，部分品种 `RT_AMT` 为 0，属正常情况。

## 2. 资产分类与逻辑 API 类型映射

### 2.1 指数（全球 & A 股）
- 代码示例：`000001.SH`, `000300.SH`, `000852.SH`, `HSI.HI`, `SPX.GI`, `IXIC.GI`, `N225.GI`, `FTSE.GI`, 等。
- 适用逻辑类型：
  - `GLOBAL_INDICES_SNAPSHOT`
  - `A_SHARES_INDEX_SNAPSHOT`
- 字段映射建议：
  - `symbol` = WindCodes
  - `last` = RT_LAST
  - `change` = RT_CHG
  - `pct_change` = RT_PCT_CHG
  - `open/high/low/prev_close` = RT_OPEN/RT_HIGH/RT_LOW/RT_PRE_CLOSE
  - `volume/amount` = RT_VOL/RT_AMT（部分境外指数量级或为 0）
  - `last_update` = 合并 RT_DATE + RT_TIME（注意时区）

### 2.2 外汇
- 代码示例：`USDCNH.FX`, `EURUSD.FX`, `USDJPY.FX`, `USDX.FX`, `USDCNY.IB` 等。
- 适用逻辑类型：`FX_SNAPSHOT`
- 字段映射建议：
  - `pair` = WindCodes
  - `mid` 或 `last` = RT_LAST
  - `pct_change_24h` = RT_PCT_CHG
  - 其他成交类字段可忽略。

### 2.3 政策利率 / 短端利率
- 代码示例：`LPR1Y.IR`, `LPR5Y.IR`, `SHIBORON.IR`, `SHIBOR1W.IR`, `SHIBOR1M.IR`, `LIUSD3M.IR` 等。
- 适用逻辑类型：`RATES_POLICY_BENCHMARKS`
- 字段映射建议：
  - `rate_id` = WindCodes
  - `value` = RT_LAST（即当前利率水平，单位 %）
  - `change_bp` = RT_CHG * 100（若有；否则置空）
  - 其他成交/估值字段忽略。

### 2.4 国债收益率 / 期限点
- 代码示例：`TB1Y.WI`, `TB3Y.WI`, `TB5Y.WI`, `TB7Y.WI`, `TB10Y.WI`, `UST2Y.GBM`, `UST5Y.GBM`, `UST10Y.GBM`, `UST30Y.GBM` 等。
- 适用逻辑类型：
  - `YIELD_CURVE_CN`（TB*）
  - `YIELD_CURVE_US`（UST*）
- 字段映射建议：
  - `tenor` 可由代码映射（1Y/3Y/5Y/7Y/10Y/30Y）
  - `yield` = RT_LAST
  - `yield_prev` 或 `change_bp` 可由 RT_PRE_CLOSE/RT_CHG 计算（如需要）
  - 其他成交字段忽略。

### 2.5 信用债 / 政策性金融债（AAA 等）
- 代码示例：`CDB10Y.WI`, `CDB5Y.WI`, `CDBS10Y.WI`, `EXIMB10Y.WI`, `NCDB*` 等。
- 适用逻辑类型：`CREDIT_CURVE_CN_AAA`（或拓展为“政策性金融债/信用曲线”）
- 字段映射建议与国债收益率相同（`yield` = RT_LAST，其他成交字段忽略）。
- 注意：这些行在 CSV 中成交/广度为 0，属于正常情况。

### 2.6 商品期货（国内 + 国际）

- 代码示例：  
  - 国际：`GC.CMX`（COMEX Gold）、`SI.CMX`（COMEX Silver）、`HG.CMX`（COMEX Copper）、`CL.NYM`（NYMEX Crude）、`NG.NYM`（NYMEX NatGas）等。  
  - 国内：`TA.CZC`（PTA）、`J.DCE`（焦炭）、`SA.CZC`（纯碱）、`LH.DCE`（生猪）、`RB.SHF`（螺纹钢）等。  
- 适用逻辑类型：
  - `COMMODITY_KEY_FUTURES_SNAPSHOT`
- 字段映射建议（来自 `商品期货输出示例.csv`）：
  - `symbol` = WindCodes
  - `name` = 通过符号 → 品种名称映射表补充（建议在 `docs/api_specs` 单独维护一个 CSV）
  - `last` = RT_LAST
  - `change` = RT_CHG
  - `pct_change` = RT_PCT_CHG
  - `high` / `low` / `open` / `prev_close` = RT_HIGH / RT_LOW / RT_OPEN / RT_PRE_CLOSE
  - `volume` = RT_VOL（如果非 0）
  - `last_update` = RT_DATE + RT_TIME
  - 其他字段：`RT_AMT`, `RT_LAST_AMT`, `RT_LAST_VOL` 可按需要补充为成交额/最近成交量等（允许为 0）。

> 如果后续需要按照“板块/品类”做 `COMMODITY_SECTOR_HEATMAP`（比如能源、有色、农产品），可以在内部维护一张「品种 → 板块」映射表，将上述期货快照聚合到板块层。

## 3. 解析与规范化建议

1. **分类规则**（可在 Provider 层硬编码或用映射表）：
   - 后缀 `.FX` → `FX_SNAPSHOT`
   - `.IR` → `RATES_POLICY_BENCHMARKS`
   - `.WI` 或 `.GBM` → 国债/金融债收益率（`YIELD_CURVE_CN` / `YIELD_CURVE_US` / `CREDIT_CURVE_CN_AAA`）
   - 期货：交易所后缀 `.SHF` / `.DCE` / `.CZC` / `.CME` / `.NYM` / `.CMX` / `.CBT` 等 → `COMMODITY_KEY_FUTURES_SNAPSHOT`
   - `.GI`, `.HI`, `.CSI`, `.SH`, `.SZ`, `.BJ` → 各类指数（`GLOBAL_INDICES_SNAPSHOT` / `A_SHARES_INDEX_SNAPSHOT`）

2. **时间戳**：将 `RT_DATE` + `RT_TIME` 合并为 ISO 字符串；时区请按 Wind 返回的时区或本地时区处理。

3. **空值/0 值处理**：
   - 对于利率/收益率类资产，成交、估值字段通常为 0，直接丢弃或置为 `null`。
   - 对于指数/FX，如果成交为 0 但价格存在，仍可作为有效快照。

4. **映射到统一 schema**：按 `data-api-requirements_zh.md` 中的逻辑类型返回结构化 JSON，确保相同字段名（如 `last`, `pct_change`, `yield`, `rate_id`）。

## 4. 对接下一步

- 你如果再补充单独的债券收益率/曲线代码列表，请放在 `docs/api_specs/` 里，我可以据此完善“代码 → 期限/类别”的映射表。
- 按上述分类把 Wind 文档或接口说明放入 `docs/api_specs/wind/`（建议新建），然后后端 Provider 可以直接实现对 `w.wsq` 回调的解析与归类。 
