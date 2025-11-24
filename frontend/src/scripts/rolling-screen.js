import { fetchLatestSnapshot } from "./dataClient.js";

const SCENES = [
  "page-global",
  "page-ashares",
  "page-short",
  "page-macro",
  "page-commodities",
  "page-alt",
  "page-events",
];
const SCENE_NAMES = {
  "page-global": "全球指数概览",
  "page-ashares": "A股市场概览",
  "page-short": "A股短线资金聚焦",
  "page-macro": "债券与宏观",
  "page-commodities": "大宗商品市场",
  "page-alt": "另类与数字资产",
  "page-events": "市场大事倒计时",
};

const REGION_GROUPS = [
  {
    id: "asia",
    label: "亚洲",
    codes: ["000001.SH", "399001.SZ", "399006.SZ", "HSI.HI", "N225.GI"],
  },
  {
    id: "americas",
    label: "北美",
    codes: ["DJI.GI", "SPX.GI", "IXIC.GI", "NDXTMC.GI"],
  },
  {
    id: "europe",
    label: "欧洲",
    codes: ["SX5E.GI", "UKX.GI", "CAC.GI", "DAX.GI"],
  },
];

const CORE_A_SHARES = [
  { code: "000001.SH", name: "上证综指" },
  { code: "399001.SZ", name: "深证成指" },
  { code: "399006.SZ", name: "创业板指" },
  { code: "000300.SH", name: "沪深300" },
];

const RATE_LABELS = {
  "M0000017.SH": "中国国债10Y",
  "M0000025.SH": "中国国债5Y",
  "M0000007.SH": "中国国债3Y",
  "M0000001.SH": "中国国债1Y",
  "UST10Y.GBM": "美债10Y",
  "UST5Y.GBM": "美债5Y",
  "UST2Y.GBM": "美债2Y",
  "UST3M.GBM": "美债3M",
  "TB10Y.WI": "国开10Y",
  "TB5Y.WI": "国开5Y",
  "LPR1Y.IR": "LPR 1Y",
  "LPR5Y.IR": "LPR 5Y",
  "SOFR.IR": "SOFR 隔夜",
  "SONIA.IR": "SONIA 隔夜",
  "EFFR.IR": "美国联邦基金",
};

const YIELD_CURVE_SERIES = [
  {
    key: "cn",
    label: "中国国债曲线",
    color: "#6dd3ff",
    points: [
      { code: "M0000001.SH", tenor: 1, label: "1Y" },
      { code: "M0000007.SH", tenor: 3, label: "3Y" },
      { code: "M0000025.SH", tenor: 5, label: "5Y" },
      { code: "M0000017.SH", tenor: 10, label: "10Y" },
    ],
  },
  {
    key: "us",
    label: "美国国债曲线",
    color: "#f7b66b",
    points: [
      { code: "UST3M.GBM", tenor: 0.25, label: "3M" },
      { code: "UST5Y.GBM", tenor: 5, label: "5Y" },
      { code: "UST10Y.GBM", tenor: 10, label: "10Y" },
    ],
  },
];

const FX_LABELS = {
  "USDCNY.EX": "USD/CNY",
  "USDCNH.FX": "USD/CNH",
  "EURCNY.EX": "EUR/CNY",
  "EURUSD.FX": "EUR/USD",
  "USDJPY.FX": "USD/JPY",
  "USDX.FX": "DXY",
  "HKDCNY.EX": "HKD/CNY",
  "GBPUSD.FX": "GBP/USD",
};

const COMMODITY_SECTORS = {
  "RB.SHF": "黑色金属",
  "RB00.SHF": "黑色金属",
  "I00.DCE": "黑色金属",
  "CU00.SHF": "基本金属",
  "AL00.SHF": "基本金属",
  "ZN00.SHF": "基本金属",
  "HG.CMX": "基本金属",
  "GC.CMX": "贵金属",
  "SI.CMX": "贵金属",
  "PL.NYM": "贵金属",
  "PA.NYM": "贵金属",
  "CL.NYM": "能源",
  "COIL.BR": "能源",
  "NG.NYM": "能源",
  "ZC.CBT": "农产品",
  "ZS.CBT": "农产品",
  "KC.NYB": "软商品",
  "TA.CZC": "化工",
  "PTA.CZC": "化工",
  "AU00.SHF": "贵金属",
};

class RollingScreenController {
  constructor() {
    this.pageIndex = 0;
    this.lastUpdate = null;
    this.rotationMs = 10_000;
    this.rotationTimer = null;
    this.dataTimer = null;
    this.isConnected = false;
    this.countdownTimer = null;
    this.nextEventTime = null;

    this.cache = {
      snapshot: null,
      events: [],
      upcomingEvents: [],
    };

    this.setupElements();
    this.setupPageDots();
    this.startClock();
    this.startRotation();
    this.startDataLoop();
  }

  setupElements() {
    this.elements = {
      pages: SCENES.map((id) => document.getElementById(id)),
      pageDots: document.getElementById("page-dots"),
      pageLabel: document.getElementById("current-page-label"),
      dataMode: document.getElementById("meta-data-mode"),
      lastUpdate: document.getElementById("meta-last-update"),
      localClock: document.getElementById("meta-clock"),
      regionList: document.getElementById("region-list"),
      leaderboard: document.getElementById("leaderboard-body"),
      aSharesGrid: document.getElementById("ashares-grid"),
      metrics: {
        advancing: document.getElementById("metric-advancing"),
        declining: document.getElementById("metric-declining"),
        unchanged: document.getElementById("metric-unchanged"),
      },
      heatmap: document.getElementById("heatmap-grid"),
      usFocus: document.getElementById("us-focus-list"),
      ticker: document.getElementById("ticker-track"),
      connectionDot: document.getElementById("connection-dot"),
      connectionText: document.getElementById("connection-text"),
      shortGainers: document.getElementById("short-gainers"),
      shortDecliners: document.getElementById("short-decliners"),
      shortHeatmap: document.getElementById("short-heatmap"),
      ratesList: document.getElementById("rates-list"),
      yieldCurves: document.getElementById("yield-curves"),
      macroInsights: document.getElementById("macro-insights"),
      commodityGroups: document.getElementById("commodity-groups"),
      commodityNotes: document.getElementById("commodity-notes"),
      altCrypto: document.getElementById("alt-crypto"),
      altFx: document.getElementById("alt-fx"),
      altCommodities: document.getElementById("alt-commodities"),
      altSummary: document.getElementById("alt-summary"),
      countdownTitle: document.getElementById("event-next-title"),
      countdownMeta: document.getElementById("countdown-meta"),
      eventList: document.getElementById("event-list"),
      countdownNumbers: {
        days: document.getElementById("countdown-days"),
        hours: document.getElementById("countdown-hours"),
        minutes: document.getElementById("countdown-minutes"),
        seconds: document.getElementById("countdown-seconds"),
      },
    };
  }

  setupPageDots() {
    if (!this.elements.pageDots) return;
    this.elements.pageDots.innerHTML = SCENES.map(
      (_, index) => `<div class="page-dot" data-index="${index}"></div>`
    ).join("");
    this.elements.pageDots
      .querySelectorAll(".page-dot")
      .forEach((dot, index) =>
        dot.addEventListener("click", () => {
          this.setScene(index);
          this.restartRotation();
        })
      );
    this.updatePageIndicator();
  }

  startRotation() {
    this.rotationTimer = setInterval(() => {
      this.pageIndex = (this.pageIndex + 1) % SCENES.length;
      this.updatePageIndicator();
    }, this.rotationMs);
  }

  restartRotation() {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
    }
    this.startRotation();
  }

  startDataLoop() {
    this.fetchAndRender();
    this.dataTimer = setInterval(() => this.fetchAndRender(), 30_000);
  }

  async fetchAndRender() {
    try {
      const snapshot = await fetchLatestSnapshot();
      this.cache.snapshot = snapshot;
      const snapshotTime = snapshot?.timestamp ? new Date(snapshot.timestamp) : null;
      this.lastUpdate =
        snapshotTime && !Number.isNaN(snapshotTime.getTime())
          ? snapshotTime
          : new Date();
      this.setConnectionStatus(true);
      this.updateHeader(snapshot);
      this.renderGlobalScene(snapshot);
      this.renderASharesScene(snapshot);
      this.renderShortTermScene(snapshot);
      this.renderMacroScene(snapshot);
      this.renderCommoditiesScene(snapshot);
      this.renderAltScene(snapshot);
      this.renderEventsScene(snapshot);
      this.updateTicker(snapshot);
    } catch (error) {
      console.error("Failed to retrieve snapshot for rolling screen", error);
      this.setConnectionStatus(false);
    }
  }

  startClock() {
    const tick = () => {
      if (this.elements.localClock) {
        const now = new Date();
        this.elements.localClock.textContent = now.toLocaleTimeString("zh-CN", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
      }
    };
    tick();
    setInterval(tick, 1000);
  }

  setScene(index) {
    this.pageIndex = index % SCENES.length;
    this.updatePageIndicator();
  }

  updatePageIndicator() {
    SCENES.forEach((sceneId, idx) => {
      const el = document.getElementById(sceneId);
      if (el) {
        el.classList.toggle("active", idx === this.pageIndex);
      }

      const dot = this.elements.pageDots?.querySelector(
        `.page-dot[data-index="${idx}"]`
      );
      if (dot) {
        dot.classList.toggle("active", idx === this.pageIndex);
      }
    });

    if (this.elements.pageLabel) {
      const sceneId = SCENES[this.pageIndex];
      this.elements.pageLabel.textContent =
        SCENE_NAMES[sceneId] ?? "未知场景";
    }
  }

  updateHeader(snapshot) {
    const mode =
      snapshot?.data_mode ??
      snapshot?.metadata?.data_mode ??
      snapshot?.dataMode ??
      "mock";
    if (this.elements.dataMode) {
      this.elements.dataMode.textContent = mode.toUpperCase();
    }

    if (this.elements.lastUpdate) {
      const label = this.lastUpdate
        ? this.lastUpdate.toLocaleTimeString("zh-CN", {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })
        : "--:--:--";
      this.elements.lastUpdate.textContent = label;
    }
  }

  renderGlobalScene(snapshot) {
    this.renderRegions(snapshot);
    this.renderLeaders(snapshot);
    this.renderUsFocus(snapshot);
  }

  renderRegions(snapshot) {
    if (!this.elements.regionList) return;
    const indices = snapshot?.indices ?? {};
    if (!indices || Object.keys(indices).length === 0) {
      this.elements.regionList.innerHTML =
        '<div class="region-card">暂无指数数据</div>';
      return;
    }

    const cards = REGION_GROUPS.map((region) => {
      const entries = region.codes
        .map((code) => ({ code, data: indices[code] }))
        .filter((item) => item.data && typeof item.data === "object");

      if (!entries.length) {
        return `
          <div class="region-card">
            <div class="region-header">
              <div>${region.label}</div>
              <div class="region-score">--</div>
            </div>
            <div class="region-desc">等待数据...</div>
          </div>
        `;
      }

      const avg =
        entries.reduce(
          (sum, item) => sum + (Number(item.data.change_pct) || 0),
          0
        ) / entries.length;
      const score = Math.max(5, Math.min(95, Math.round(50 + avg * 100)));
      const sentiment = avg >= 0 ? "风险偏好回升" : "避险需求走强";
      const list = entries
        .map(
          (entry) => `
            <div class="index-item">
              <span>${entry.data.display_name ?? entry.code}</span>
              <span class="index-change ${
                entry.data.change_pct >= 0 ? "positive" : "negative"
              }">
                ${this.formatChange(entry.data.change_pct)}%
              </span>
            </div>
          `
        )
        .join("");

      return `
        <div class="region-card">
          <div class="region-header">
            <div>${region.label}</div>
            <div class="region-score">${score}</div>
          </div>
          <div class="region-desc">${sentiment}</div>
          <div class="index-list">${list}</div>
        </div>
      `;
    });

    this.elements.regionList.innerHTML = cards.join("");
  }

  renderLeaders(snapshot) {
    if (!this.elements.leaderboard) return;
    const rows = Object.entries(snapshot?.indices ?? {})
      .filter(([code]) => this.isIndexCode(code))
      .filter(([, data]) => data && typeof data === "object")
      .sort(
        (a, b) =>
          Math.abs(b[1].change_pct ?? 0) - Math.abs(a[1].change_pct ?? 0)
      )
      .slice(0, 8)
      .map(([code, data]) => {
        const pct = data.change_pct ?? 0;
        const cls = pct >= 0 ? "positive" : "negative";
        return `
          <tr>
            <td>${data.display_name ?? data.name ?? code}</td>
            <td>${this.formatNumber(data.last)}</td>
            <td class="${cls}">${this.formatChange(pct)}%</td>
          </tr>
        `;
      });

    this.elements.leaderboard.innerHTML =
      rows.join("") || `<tr><td colspan="3">暂无数据</td></tr>`;
  }

  renderUsFocus(snapshot) {
    if (!this.elements.usFocus) return;
    const usEntries = Object.entries(snapshot?.us_stocks ?? {})
      .filter(
        ([code, data]) =>
          data && typeof data === "object" && this.isUsEquityCode(code)
      )
      .sort(
        (a, b) =>
          Math.abs(b[1].change_pct ?? 0) - Math.abs(a[1].change_pct ?? 0)
      )
      .slice(0, 5);

    if (!usEntries.length) {
      this.elements.usFocus.innerHTML = `<div class="board-item">暂无美股数据</div>`;
      return;
    }

    this.elements.usFocus.innerHTML = usEntries
      .map(([code, data]) => {
        const pct = data.change_pct ?? 0;
        const cls = pct >= 0 ? "positive" : "negative";
        const price = this.isNumber(data.last)
          ? `$${this.formatNumber(data.last)}`
          : "--";
        return `
          <div class="board-item">
            <div>
              <div class="board-name">${data.display_name ?? data.name ?? code}</div>
              <div class="board-meta">${code} · ${price}</div>
            </div>
            <div class="${cls}">${this.formatChange(pct)}%</div>
          </div>
        `;
      })
      .join("");
  }

  renderASharesScene(snapshot) {
    this.renderCoreIndices(snapshot);
    this.renderMetrics(snapshot?.summary);
    const boardHeatmap = this.buildBoardHeatmap(snapshot?.a_share_short_term);
    const fallbackHeatmap = snapshot?.a_share_heatmap ?? [];
    this.renderHeatmap(boardHeatmap.length ? boardHeatmap : fallbackHeatmap);
  }

  renderShortTermScene(snapshot) {
    const shortData = snapshot?.a_share_short_term ?? {};
    const hotBoards = Array.isArray(shortData.hot_boards)
      ? shortData.hot_boards
      : [];
    const coldBoards = Array.isArray(shortData.cold_boards)
      ? shortData.cold_boards
      : [];
    const capitalBoards = Array.isArray(shortData.capital_boards)
      ? shortData.capital_boards
      : [];

    this.renderBoardColumn(
      this.elements.shortGainers,
      hotBoards,
      "暂无强势板块",
      { metaMode: "turnover" }
    );
    this.renderBoardColumn(
      this.elements.shortDecliners,
      coldBoards,
      "暂无回调风险",
      { metaMode: "turnover" }
    );
    this.renderBoardColumn(
      this.elements.shortHeatmap,
      capitalBoards,
      "等待资金榜数据",
      { metaMode: "flow" }
    );
  }

  renderBoardColumn(targetEl, list, emptyText, options = {}) {
    if (!targetEl) return;
    if (!Array.isArray(list) || !list.length) {
      targetEl.innerHTML = `<div class="board-item">${emptyText}</div>`;
      return;
    }
    const { metaMode } = options;
    targetEl.innerHTML = list
      .map((item) => {
        const pct = item?.change_pct ?? 0;
        const cls = pct >= 0 ? "positive" : "negative";
        const displayName = item?.display_name ?? item?.name ?? item?.code ?? "--";
        const metaText = this.buildBoardMeta(item, metaMode);
        return `
          <div class="board-item">
            <div>
              <div class="board-name">${displayName}</div>
              <div class="board-meta">${metaText}</div>
            </div>
            <div class="${cls}">${this.formatChange(pct)}%</div>
          </div>
        `;
      })
      .join("");
  }

  buildBoardMeta(item, mode) {
    if (!item) {
      return "--";
    }
    if (mode === "flow") {
      const flow = item.net_flow;
      if (this.isNumber(flow)) {
        return `净流入 ${this.formatFlow(flow)}`;
      }
    }
    if (mode === "turnover" && this.isNumber(item.turnover_rate)) {
      return `换手 ${this.formatNumber(item.turnover_rate, 1)}%`;
    }
    return item.code ?? "--";
  }

  renderMacroScene(snapshot) {
    const rates = snapshot?.rates ?? {};
    const fx = snapshot?.fx ?? {};

    if (this.elements.ratesList) {
      const orderedCodes = [
        "M0000017.SH",
        "M0000025.SH",
        "M0000007.SH",
        "M0000001.SH",
        "UST10Y.GBM",
        "UST2Y.GBM",
        "UST5Y.GBM",
        "SOFR.IR",
        "SONIA.IR",
        "EFFR.IR",
      ];
      const rateEntries = orderedCodes
        .map((code) => [code, rates[code]])
        .filter(([, data]) => data && typeof data === "object");

      this.elements.ratesList.innerHTML = rateEntries.length
        ? rateEntries
            .map(([code, data]) => {
              const change = data.change ?? 0;
              const cls = change >= 0 ? "positive" : "negative";
              return `
                <div class="rate-row">
                  <div class="rate-name">${this.getRateName(code)}</div>
                  <div class="rate-value">${this.formatNumber(data.last, 2)}%</div>
                  <div class="rate-change ${cls}">${this.formatChange(change, 2)}</div>
                </div>
              `;
            })
            .join("")
        : `<div class="rate-row">暂无利率数据</div>`;
    }

    this.renderYieldCurves(rates);

    if (this.elements.macroInsights) {
      const cn10y = this.getRateValue(rates, "M0000017.SH");
      const cn5y = this.getRateValue(rates, "M0000025.SH");
      const us10y = this.getRateValue(rates, "UST10Y.GBM");
      const us2y = this.getRateValue(rates, "UST2Y.GBM");
      const sofr = this.getRateValue(rates, "SOFR.IR");
      const sonia = this.getRateValue(rates, "SONIA.IR");
      const effr = this.getRateValue(rates, "EFFR.IR");
      const usdcnh = fx?.["USDCNH.FX"];

      const cards = [
        { label: "中美10Y利差", value: this.formatSpread(cn10y, us10y) },
        { label: "国债长短端(CN)", value: this.formatSpread(cn10y, cn5y) },
        { label: "美债10Y-2Y", value: this.formatSpread(us10y, us2y) },
        { label: "SOFR 隔夜", value: this.formatRateValue(sofr) },
        { label: "SONIA 隔夜", value: this.formatRateValue(sonia) },
        { label: "EFFR", value: this.formatRateValue(effr) },
        { label: "USDCNH", value: usdcnh ? this.formatNumber(usdcnh.last, 4) : "--" },
      ];

      this.elements.macroInsights.innerHTML = cards
        .map(
          (card) => `
          <div class="stat-card">
            <span>${card.label}</span>
            <strong>${card.value}</strong>
          </div>
        `
        )
        .join("");
    }
  }

  renderCommoditiesScene(snapshot) {
    const commodities = snapshot?.commodities ?? {};
    if (this.elements.commodityGroups) {
      const grouped = {};
      Object.entries(commodities).forEach(([code, data]) => {
        if (!data || typeof data !== "object") return;
        const sector = this.getCommoditySector(code);
        grouped[sector] = grouped[sector] ?? [];
        grouped[sector].push({ code, data });
      });

      const html = Object.entries(grouped)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([sector, items]) => {
          const rows = items
            .sort(
              (a, b) =>
                Math.abs(b.data.change_pct ?? 0) - Math.abs(a.data.change_pct ?? 0)
            )
            .map(
              ({ code, data }) => `
              <div class="commodity-item">
                <span>${data.display_name ?? data.name ?? code}</span>
                <span class="${(data.change_pct ?? 0) >= 0 ? "positive" : "negative"}">
                  ${this.formatChange(data.change_pct)}%
                </span>
              </div>
            `
            )
            .join("");

          return `
            <div class="commodity-group">
              <div class="commodity-title">${sector}</div>
              <div class="commodity-items">${rows}</div>
            </div>
          `;
        })
        .join("");

      this.elements.commodityGroups.innerHTML =
        html || `<div class="commodity-group">暂无大宗商品数据</div>`;
    }

    if (this.elements.commodityNotes) {
      const items = Object.entries(commodities).filter(
        ([, data]) => data && typeof data === "object"
      );
      if (!items.length) {
        this.elements.commodityNotes.innerHTML = `<p>等待大宗商品行情...</p>`;
        return;
      }

      const topGain = items
        .slice()
        .sort(
          (a, b) =>
            (b[1].change_pct ?? 0) - (a[1].change_pct ?? 0)
        )[0];
      const topDrop = items
        .slice()
        .sort(
          (a, b) =>
            (a[1].change_pct ?? 0) - (b[1].change_pct ?? 0)
        )[0];

      const notes = [
        `覆盖品种：${items.length} 个`,
        topGain
          ? `涨幅领先：${topGain[1].display_name ?? topGain[0]} (${this.formatChange(
              topGain[1].change_pct
            )}%)`
          : null,
        topDrop
          ? `回调焦点：${topDrop[1].display_name ?? topDrop[0]} (${this.formatChange(
              topDrop[1].change_pct
            )}%)`
          : null,
      ].filter(Boolean);

      this.elements.commodityNotes.innerHTML = notes.map((n) => `<p>${n}</p>`).join("");
    }
  }

  renderAltScene(snapshot) {
    const crypto = snapshot?.crypto ?? {};
    const fx = snapshot?.fx ?? {};
    const commodities = snapshot?.commodities ?? {};

    if (this.elements.altCrypto) {
      const cryptoEntries = Object.entries(crypto)
        .filter(([, data]) => data && typeof data === "object")
        .sort(
          (a, b) =>
            Math.abs(b[1].change_pct ?? 0) - Math.abs(a[1].change_pct ?? 0)
        )
        .slice(0, 6);

      this.elements.altCrypto.innerHTML = cryptoEntries.length
        ? cryptoEntries
            .map(([code, data]) => {
              const pct = data.change_pct ?? 0;
              const cls = pct >= 0 ? "positive" : "negative";
              return `
                <div class="crypto-card">
                  <div class="symbol">${data.display_name ?? data.name ?? code}</div>
                  <div class="price">$${this.formatNumber(data.last, 2)}</div>
                  <div class="change ${cls}">${this.formatChange(pct)}%</div>
                </div>
              `;
            })
            .join("")
        : `<div class="loading-spinner">暂无数字资产数据</div>`;
    }

    if (this.elements.altCommodities) {
      const commodityEntries = Object.entries(commodities)
        .filter(([, data]) => data && typeof data === "object")
        .sort(
          (a, b) =>
            Math.abs(b[1].change_pct ?? 0) - Math.abs(a[1].change_pct ?? 0)
        )
        .slice(0, 5);

      this.elements.altCommodities.innerHTML = commodityEntries.length
        ? commodityEntries
            .map(([code, data]) => {
              const pct = data.change_pct ?? 0;
              const cls = pct >= 0 ? "positive" : "negative";
              return `
                <div class="board-item">
                  <div>
                    <div class="board-name">${data.display_name ?? data.name ?? code}</div>
                    <div class="board-meta">${code}</div>
                  </div>
                  <div class="${cls}">${this.formatChange(pct)}%</div>
                </div>
              `;
            })
            .join("")
        : `<div class="board-item">暂无大宗/避险数据</div>`;
    }

    if (this.elements.altFx) {
      const watchlist = ["USDCNH.FX", "USDCNY.EX", "EURUSD.FX", "USDJPY.FX", "USDX.FX", "GBPUSD.FX"];
      const fxEntries = watchlist
        .map((code) => [code, fx[code]])
        .filter(([, data]) => data && typeof data === "object");

      this.elements.altFx.innerHTML = fxEntries.length
        ? fxEntries
            .map(([code, data]) => {
              const pct = data.change_pct ?? 0;
              const cls = pct >= 0 ? "positive" : "negative";
              return `
                <div class="fx-card">
                  <div class="pair">${this.getFXName(code)}</div>
                  <div class="value">${this.formatNumber(data.last, 4)}</div>
                  <div class="change ${cls}">${this.formatChange(pct)}%</div>
                </div>
              `;
            })
            .join("")
        : `<div class="loading-spinner">暂无外汇数据</div>`;
    }

    if (this.elements.altSummary) {
      const btc = crypto["BTC.CC"];
      const eth = crypto["ETH.CC"];
      const gold = commodities["GC.CMX"];
      const oil = commodities["CL.NYM"] ?? commodities["COIL.BR"];
      const cards = [
        { label: "BTC 24H", value: btc ? `${this.formatChange(btc.change_pct)}%` : "--" },
        { label: "ETH 24H", value: eth ? `${this.formatChange(eth.change_pct)}%` : "--" },
        { label: "COMEX 黄金", value: gold ? `$${this.formatNumber(gold.last, 2)}` : "--" },
        { label: "WTI/Brent", value: oil ? `$${this.formatNumber(oil.last, 2)}` : "--" },
      ];

      this.elements.altSummary.innerHTML = cards
        .map(
          (card) => `
          <div class="stat-card">
            <span>${card.label}</span>
            <strong>${card.value}</strong>
          </div>
        `
        )
        .join("");
    }
  }

  renderEventsScene(snapshot) {
    const rawEvents = snapshot?.calendar?.events ?? [];
    const normalizedEvents = this.normalizeEvents(rawEvents);
    const upcomingEvents = this.filterUpcomingEvents(normalizedEvents);
    this.cache.events = normalizedEvents;
    this.cache.upcomingEvents = upcomingEvents;

    if (this.elements.eventList) {
      if (!upcomingEvents.length) {
        this.elements.eventList.innerHTML = `<div class="event-item">暂无未来事件</div>`;
      } else {
        const html = upcomingEvents
          .slice(0, 6)
          .map((evt) => {
            const timeLabel = this.formatEventTimestamp(evt.eventDate);
            const importance = evt.importance ?? "";
            return `
              <div class="event-item">
                <strong>${evt.title ?? evt.event_id ?? "事件"}</strong><br/>
                时间：${timeLabel}　|　地区：${evt.country ?? "--"}　|　重要性：${importance}
              </div>
            `;
          })
          .join("");
        this.elements.eventList.innerHTML = html;
      }
    }

    const upcoming = upcomingEvents[0] ?? null;

    if (this.elements.countdownTitle) {
      this.elements.countdownTitle.textContent = upcoming
        ? `下一事件：${upcoming.title ?? upcoming.event_id}`
        : "下一事件：待定";
    }

    if (this.elements.countdownMeta) {
      this.elements.countdownMeta.textContent = upcoming
        ? `${this.formatEventTimestamp(upcoming.eventDate)} | ${
            upcoming.country ?? "--"
          }`
        : "暂无即将发生的事件";
    }

    this.startCountdown(upcoming?.eventDate ?? null);
  }

  renderCoreIndices(snapshot) {
    if (!this.elements.aSharesGrid) return;
    const aShares = snapshot?.a_shares ?? {};
    const cards = CORE_A_SHARES.map((item) => {
      const data = aShares[item.code];
      if (!data) {
        return `
          <div class="ashares-card">
            <div class="ashares-header">
              <span>${item.name}</span>
              <span>${item.code}</span>
            </div>
            <div class="ashares-value">--</div>
            <div class="ashares-change">--</div>
          </div>
        `;
      }

      const changePct = data.change_pct ?? 0;
      const cls = changePct >= 0 ? "positive" : "negative";
      const [integerPart, decimalPart] = this.splitValue(data.last);

      return `
        <div class="ashares-card">
          <div class="ashares-header">
            <span>${item.name}</span>
            <span>${item.code}</span>
          </div>
          <div class="ashares-value">${integerPart}<small>.${decimalPart}</small></div>
          <div class="ashares-change ${cls}">
            ${this.formatChange(data.change)} (${this.formatChange(changePct)}%)
          </div>
        </div>
      `;
    });

    this.elements.aSharesGrid.innerHTML = cards.join("");
  }

  renderMetrics(summary = {}) {
    const { advancing = "--", declining = "--", unchanged = "--" } = summary;
    if (this.elements.metrics.advancing) {
      this.elements.metrics.advancing.textContent = advancing;
    }
    if (this.elements.metrics.declining) {
      this.elements.metrics.declining.textContent = declining;
    }
    if (this.elements.metrics.unchanged) {
      this.elements.metrics.unchanged.textContent = unchanged;
    }
  }

  buildBoardHeatmap(shortData = {}) {
    const pools = [
      ...(Array.isArray(shortData?.hot_boards) ? shortData.hot_boards : []),
      ...(Array.isArray(shortData?.cold_boards) ? shortData.cold_boards : []),
      ...(Array.isArray(shortData?.capital_boards) ? shortData.capital_boards : []),
    ];

    const seen = new Set();
    const normalized = [];
    pools.forEach((item) => {
      const code = item?.code ?? item?.name;
      if (!code || seen.has(code)) return;
      const pctValue = this.isNumber(item?.pct_change)
        ? item.pct_change
        : this.isNumber(item?.change_pct)
          ? item.change_pct
          : null;
      if (pctValue === null) return;
      seen.add(code);
      normalized.push({
        code,
        name: item.display_name ?? item.name ?? code,
        pct_change: pctValue,
      });
    });

    normalized.sort(
      (a, b) => Math.abs(b.pct_change ?? 0) - Math.abs(a.pct_change ?? 0)
    );
    return normalized.slice(0, 8);
  }

  renderHeatmap(heatmap = []) {
    if (!this.elements.heatmap) return;
    if (!heatmap.length) {
      this.elements.heatmap.innerHTML =
        '<div class="heatmap-cell">暂无热力图数据</div>';
      return;
    }

    const cells = heatmap.slice(0, 8).map((item) => {
      const pct = this.isNumber(item?.pct_change)
        ? item.pct_change
        : this.isNumber(item?.change_pct)
          ? item.change_pct
          : null;
      const cls = (pct ?? 0) >= 0 ? "positive" : "negative";
      return `
        <div class="heatmap-cell">
          <div>${item.name ?? item.display_name ?? item.code ?? "--"}</div>
          <div class="heatmap-change ${cls}">
            ${this.formatChange(pct)}%
          </div>
        </div>
      `;
    });

    this.elements.heatmap.innerHTML = cells.join("");
  }

  updateTicker(snapshot) {
    if (!this.elements.ticker) return;
    const normalizedEvents =
      this.cache.events && this.cache.events.length
        ? this.cache.events
        : this.normalizeEvents(snapshot?.calendar?.events ?? []);
    const upcomingEvents =
      this.cache.upcomingEvents && this.cache.upcomingEvents.length
        ? this.cache.upcomingEvents
        : this.filterUpcomingEvents(normalizedEvents);

    if (!upcomingEvents.length) {
      this.elements.ticker.innerHTML =
        '<span class="ticker-item">暂无未来财经事件</span>';
      return;
    }

    const items = upcomingEvents
      .map(
        (evt) => `<span class="ticker-item">${this.formatEventTimestamp(
          evt.eventDate
        )} · ${evt.title ?? evt.event_id} (${evt.country ?? "--"})</span>`
      )
      .join("");

    this.elements.ticker.innerHTML = items;
  }

  setConnectionStatus(connected) {
    this.isConnected = connected;
    if (this.elements.connectionDot) {
      this.elements.connectionDot.style.background = connected
        ? "var(--positive)"
        : "var(--negative)";
    }
    if (this.elements.connectionText) {
      this.elements.connectionText.textContent = connected ? "实时" : "离线";
    }
  }

  formatNumber(value, decimals = 2) {
    if (value === undefined || value === null || isNaN(value)) {
      return "--";
    }
    return Number(value).toFixed(decimals);
  }

  formatChange(value, decimals = 2) {
    if (value === undefined || value === null || isNaN(value)) {
      return "--";
    }
    const num = Number(value).toFixed(decimals);
    return Number(value) >= 0 ? `+${num}` : num;
  }

  formatFlow(value) {
    if (value === undefined || value === null || isNaN(value)) {
      return "--";
    }
    const num = Number(value);
    const decimals = Math.abs(num) >= 100 ? 0 : 1;
    const formatted = num.toFixed(decimals);
    return `${num >= 0 ? "+" : ""}${formatted}亿`;
  }

  formatRateValue(value) {
    if (!this.isNumber(value)) {
      return "--";
    }
    return `${this.formatNumber(value, 2)}%`;
  }

  formatSpread(base, compare) {
    if (!this.isNumber(base) || !this.isNumber(compare)) {
      return "--";
    }
    const diff = (base - compare) * 100;
    const formatted = diff.toFixed(0);
    return `${diff >= 0 ? "+" : ""}${formatted} bp`;
  }

  getRateValue(rates, code) {
    const value = rates?.[code]?.last;
    return typeof value === "number" ? value : null;
  }

  renderYieldCurves(rates) {
    if (!this.elements.yieldCurves) return;

    const cards = YIELD_CURVE_SERIES.map((curve) => {
      const points = curve.points
        .map((p) => ({ ...p, value: this.getRateValue(rates, p.code) }))
        .filter((p) => this.isNumber(p.value));

      if (points.length < 2) {
        return null;
      }

      const latest = points[points.length - 1].value;
      const svg = this.buildSparkline(points, curve.color);
      return `
        <div class="yield-curve-card">
          <div class="yield-curve-header">
            <span class="label">${curve.label}</span>
            <span class="value">${this.formatNumber(latest, 2)}%</span>
          </div>
          ${svg}
        </div>
      `;
    }).filter(Boolean);

    this.elements.yieldCurves.innerHTML =
      cards.length > 0
        ? cards.join("")
        : `<div class="yield-curve-placeholder">暂无收益率曲线数据</div>`;
  }

  buildSparkline(points, color = "#6dd3ff") {
    const width = 240;
    const height = 90;
    const padding = 8;
    const sorted = [...points].sort((a, b) => a.tenor - b.tenor);
    const minTenor = Math.min(...sorted.map((p) => p.tenor));
    const maxTenor = Math.max(...sorted.map((p) => p.tenor));
    const minVal = Math.min(...sorted.map((p) => p.value));
    const maxVal = Math.max(...sorted.map((p) => p.value));
    const tenorRange = Math.max(maxTenor - minTenor, 0.1);
    const valueRange = Math.max(maxVal - minVal, 0.1);

    const coords = sorted.map((p) => {
      const x =
        padding +
        ((p.tenor - minTenor) / tenorRange) * (width - padding * 2);
      const y =
        height -
        padding -
        ((p.value - minVal) / valueRange) * (height - padding * 2);
      return { x, y, label: p.label, value: p.value };
    });

    const path = coords
      .map((pt, idx) => `${idx === 0 ? "M" : "L"}${pt.x.toFixed(1)},${pt.y.toFixed(1)}`)
      .join(" ");

    const circles = coords
      .map(
        (pt) =>
          `<circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(
            1
          )}" r="3" fill="${color}" />`
      )
      .join("");

    const labels = coords
      .map(
        (pt) =>
          `<text x="${pt.x.toFixed(1)}" y="${(pt.y - 8).toFixed(
            1
          )}" fill="#9fb3d9" font-size="10" text-anchor="middle">${pt.label}</text>`
      )
      .join("");

    return `
      <svg class="yield-curve-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <path d="${path}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" />
        ${circles}
        ${labels}
      </svg>
    `;
  }

  isNumber(value) {
    return typeof value === "number" && !Number.isNaN(value);
  }

  splitValue(value) {
    if (value === undefined || value === null || isNaN(value)) {
      return ["--", "--"];
    }
    const formatted = Number(value).toFixed(2);
    const [intPart, decimal] = formatted.split(".");
    return [intPart, decimal ?? "00"];
  }

  startCountdown(targetDate) {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
    if (!targetDate || isNaN(targetDate.getTime())) {
      this.updateCountdownDisplay(null);
      return;
    }

    this.nextEventTime = targetDate;
    const tick = () => {
      const now = new Date();
      const diff = this.nextEventTime - now;
      if (diff <= 0) {
        this.updateCountdownDisplay(0);
        clearInterval(this.countdownTimer);
        this.countdownTimer = null;
        return;
      }
      this.updateCountdownDisplay(diff);
    };
    tick();
    this.countdownTimer = setInterval(tick, 1000);
  }

  updateCountdownDisplay(diffMs) {
    const numbers = this.elements.countdownNumbers;
    if (!numbers) return;

    if (diffMs === null) {
      Object.values(numbers).forEach((el) => {
        if (el) el.textContent = "--";
      });
      return;
    }

    const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (numbers.days) numbers.days.textContent = String(days).padStart(2, "0");
    if (numbers.hours) numbers.hours.textContent = String(hours).padStart(2, "0");
    if (numbers.minutes)
      numbers.minutes.textContent = String(minutes).padStart(2, "0");
    if (numbers.seconds)
      numbers.seconds.textContent = String(seconds).padStart(2, "0");
  }

  normalizeEvents(events = []) {
    return events
      .map((evt) => {
        const eventDate = evt?.datetime ? new Date(evt.datetime) : null;
        if (!eventDate || Number.isNaN(eventDate.getTime())) {
          return null;
        }
        return { ...evt, eventDate };
      })
      .filter(Boolean)
      .sort((a, b) => a.eventDate - b.eventDate);
  }

  filterUpcomingEvents(events = []) {
    const now = new Date();
    return events.filter((evt) => evt.eventDate && evt.eventDate >= now);
  }

  formatEventTimestamp(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
      return "--";
    }
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  getRateName(code) {
    return RATE_LABELS[code] ?? code;
  }

  getFXName(code) {
    return FX_LABELS[code] ?? code;
  }

  getCommoditySector(code) {
    return COMMODITY_SECTORS[code] ?? "综合板块";
  }

  isIndexCode(code) {
    return (
      typeof code === "string" &&
      (code.endsWith(".GI") ||
        code.endsWith(".HI") ||
        code.endsWith(".SH") ||
        code.endsWith(".SZ") ||
        code.endsWith(".CSI"))
    );
  }

  isAShareCode(code) {
    return typeof code === "string" && (code.endsWith(".SH") || code.endsWith(".SZ"));
  }

  isUsEquityCode(code) {
    if (typeof code !== "string") return false;
    return (
      code.endsWith(".O") ||
      code.endsWith(".N") ||
      code.endsWith(".UW") ||
      code.endsWith(".UN") ||
      code.endsWith(".US")
    );
  }
}

window.addEventListener("DOMContentLoaded", () => {
  window.rollingScreen = new RollingScreenController();
});
