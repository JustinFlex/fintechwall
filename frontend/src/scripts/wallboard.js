/**
 * Wind Market Wallboard Controller
 * Implements the carousel-based multi-scene wallboard following product requirements
 */

import { API_BASE, fetchLatestSnapshot } from "./dataClient.js";
const CAROUSEL_INTERVAL = 25_000; // default dwell time in ms
const scenes = ["scene-a", "scene-b", "scene-c", "scene-d", "scene-e"];

class WallboardController {
  constructor() {
    this.activeIndex = 0;
    this.intervalId = null;
    this.lastDataUpdate = null;
    this.isConnected = false;
    this.currentData = {};

    this.initializeElements();
    this.startCarousel();
    this.startDataRefresh();
  }

  initializeElements() {
    this.elements = {
      marquee: document.getElementById('marquee'),
      indicesMini: document.getElementById('indices-mini'),
      fxMini: document.getElementById('fx-mini'),
      indicesDetailed: document.getElementById('indices-detailed'),
      usStocksGrid: document.getElementById('us-stocks-grid'),
      ratesGrid: document.getElementById('rates-grid'),
      commoditiesGrid: document.getElementById('commodities-grid'),
      newsBanner: document.getElementById('news-banner'),
      advancingCount: document.getElementById('advancing-count'),
      decliningCount: document.getElementById('declining-count'),
      unchangedCount: document.getElementById('unchanged-count'),
      statusDataMode: document.getElementById('status-data-mode'),
      statusLastUpdate: document.getElementById('status-last-update'),
      statusConnection: document.getElementById('status-connection'),
      statusFreshness: document.getElementById('status-freshness'),
      currentTime: document.getElementById('current-time'),
      currentSceneLabel: document.getElementById('current-scene-label'),
      connectionStatus: document.getElementById('connection-status'),
      sceneDots: document.querySelectorAll('.dot'),
      headerDataMode: document.getElementById('data-mode-pill'),
      headerLastUpdate: document.getElementById('last-update-pill')
    };

    this.startClock();
    this.initializeSceneIndicators();
  }

  startCarousel() {
    this.cycleScenes();
    this.intervalId = setInterval(() => this.cycleScenes(), CAROUSEL_INTERVAL);
  }

  cycleScenes() {
    const visibleScene = scenes[this.activeIndex % scenes.length];
    const sceneLabels = {
      'scene-a': 'Global Overview',
      'scene-b': 'Market Heatmap',
      'scene-c': 'Macro & Rates',
      'scene-d': 'US Markets',
      'scene-e': 'News & Alerts'
    };

    // Update scene visibility
    document.querySelectorAll(".scene").forEach((scene) => {
      scene.classList.toggle("active", scene.id === visibleScene);
    });

    // Update scene indicators
    this.elements.sceneDots.forEach((dot, index) => {
      dot.classList.toggle('active', index === (this.activeIndex % scenes.length));
    });

    // Update scene label
    if (this.elements.currentSceneLabel) {
      this.elements.currentSceneLabel.textContent = sceneLabels[visibleScene] || 'Unknown Scene';
    }

    this.activeIndex += 1;
  }

  async startDataRefresh() {
    // Initial fetch
    await this.fetchSnapshot();

    // Set up periodic refresh
    setInterval(() => this.fetchSnapshot(), 30_000);
  }

  async fetchSnapshot() {
    try {
      const payload = await fetchLatestSnapshot();
      this.currentData = payload;
      const ts = payload?.timestamp ? new Date(payload.timestamp) : new Date();
      this.lastDataUpdate = ts;
      this.updateAllScenes(payload);
      this.updateStatus(payload);
      this.setConnectionStatus(true);
    } catch (error) {
      console.error("Failed to fetch snapshot", error);
      this.setConnectionStatus(false);
      this.markStale();
    }
  }

  updateAllScenes(data) {
    this.updateSceneA(data);
    this.updateSceneB(data);
    this.updateSceneC(data);
    this.updateSceneD(data);
    this.updateSceneE(data);
    this.updateMarquee(data);
  }

  updateSceneA(data) {
    // Global Overview - Key indices and FX
    this.updateIndicesMini(data.a_shares || {});
    this.updateFXMini(data.fx || {});
  }

  updateSceneB(data) {
    // Equity Heat - Detailed indices view with market stats
    this.updateIndicesDetailed(data.a_shares || {});
    this.updateMarketStats(data.summary || {});
    this.updateHeatmap(data.heatmap || []);
  }

  updateSceneC(data) {
    // Macro & Rates - Government bonds and commodities
    this.updateRates(data.rates || {});
    this.updateCommodities(data.commodities || {});
  }

  updateSceneD(data) {
    // US Stocks - American market data
    this.updateUSStocks(data.us_stocks || {});
  }

  updateSceneE(data) {
    // News Banner - Market alerts and updates
    this.updateNewsBanner(data);
    this.updateCalendar(data.calendar || {});
  }

  updateIndicesMini(indices) {
    if (!this.elements.indicesMini) return;

    if (Object.keys(indices).length === 0) {
      this.elements.indicesMini.innerHTML = '<div class="loading-spinner">No indices data</div>';
      return;
    }

    // Show top 4 indices for mini view
    const topIndices = Object.entries(indices)
      .filter(([code, data]) => data && typeof data === 'object')
      .slice(0, 4);

    const html = topIndices.map(([code, data]) => {
      const changeClass = this.getChangeClass(data.change_pct);
      return `
        <div class="mini-item ${changeClass}">
          <div class="mini-name">${data.display_name || data.name || code}</div>
          <div class="mini-value">${this.formatNumber(data.last, 2)}</div>
          <div class="mini-change">${this.formatChange(data.change_pct)}%</div>
        </div>
      `;
    }).join('');

    this.elements.indicesMini.innerHTML = html;
  }

  updateFXMini(fx) {
    if (!this.elements.fxMini) return;

    if (Object.keys(fx).length === 0) {
      this.elements.fxMini.innerHTML = '<div class="loading-spinner">No FX data</div>';
      return;
    }

    const html = Object.entries(fx)
      .filter(([code, data]) => data && typeof data === 'object')
      .slice(0, 4)
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        return `
          <div class="mini-item ${changeClass}">
            <div class="mini-name">${this.getFXName(code)}</div>
            <div class="mini-value">${this.formatNumber(data.last, 4)}</div>
            <div class="mini-change">${this.formatChange(data.change_pct)}%</div>
          </div>
        `;
      }).join('');

    this.elements.fxMini.innerHTML = html;
  }

  updateIndicesDetailed(indices) {
    if (!this.elements.indicesDetailed) return;

    if (Object.keys(indices).length === 0) {
      this.elements.indicesDetailed.innerHTML = '<div class="loading-spinner">No detailed indices</div>';
      return;
    }

    const html = Object.entries(indices)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        return `
          <div class="detailed-index ${changeClass}">
            <div class="index-header">
              <div class="index-name">${data.display_name || data.name || code}</div>
              <div class="index-code">${code}</div>
            </div>
            <div class="index-metrics">
              <div class="metric">
                <span class="metric-label">Price</span>
                <span class="metric-value">${this.formatNumber(data.last, 2)}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Change</span>
                <span class="metric-value ${changeClass}">${this.formatChange(data.change)}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Change %</span>
                <span class="metric-value ${changeClass}">${this.formatChange(data.change_pct)}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Volume</span>
                <span class="metric-value">${this.formatNumber(data.volume, 0)}B</span>
              </div>
            </div>
          </div>
        `;
      }).join('');

    this.elements.indicesDetailed.innerHTML = html;
  }

  updateUSStocks(usStocks) {
    if (!this.elements.usStocksGrid) return;

    if (Object.keys(usStocks).length === 0) {
      this.elements.usStocksGrid.innerHTML = '<div class="loading-spinner">No US stocks data</div>';
      return;
    }

    const html = Object.entries(usStocks)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        return `
          <div class="us-stock-item ${changeClass}">
            <div class="stock-name">${this.getUSStockName(code)}</div>
            <div class="stock-price">$${this.formatNumber(data.last, 2)}</div>
            <div class="stock-change ${changeClass}">${this.formatChange(data.change_pct)}%</div>
          </div>
        `;
      }).join('');

    this.elements.usStocksGrid.innerHTML = html;
  }

  updateRates(rates) {
    if (!this.elements.ratesGrid) return;

    if (Object.keys(rates).length === 0) {
      this.elements.ratesGrid.innerHTML = '<div class="loading-spinner">No rates data</div>';
      return;
    }

    const html = Object.entries(rates)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change);
        return `
          <div class="rate-item">
            <div class="rate-name">${this.getRateName(code)}</div>
            <div class="rate-value">${this.formatNumber(data.last, 3)}%</div>
            <div class="rate-change ${changeClass}">${this.formatChange(data.change, 3)}</div>
          </div>
        `;
      }).join('');

    this.elements.ratesGrid.innerHTML = html;
  }

  updateCommodities(commodities) {
    if (!this.elements.commoditiesGrid) return;

    if (Object.keys(commodities).length === 0) {
      this.elements.commoditiesGrid.innerHTML = '<div class="loading-spinner">No commodities data</div>';
      return;
    }

    const html = Object.entries(commodities)
      .filter(([code, data]) => data && typeof data === 'object')
      .slice(0, 8)
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        return `
          <div class="commodity-item">
            <div class="commodity-name">${this.getCommodityName(code)}</div>
            <div class="commodity-sector">${this.getCommoditySector(code)}</div>
            <div class="commodity-price">${this.formatNumber(data.last, 0)}</div>
            <div class="commodity-change ${changeClass}">${this.formatChange(data.change_pct)}%</div>
          </div>
        `;
      }).join('');

    this.elements.commoditiesGrid.innerHTML = html;
  }

  updateNewsBanner(data) {
    if (!this.elements.newsBanner) return;

    const events = (data.calendar && data.calendar.events) || [];
    const summaries = [];
    if (events.length) {
      events.slice(0, 3).forEach((evt) => {
        const time = evt.datetime ? new Date(evt.datetime).toLocaleTimeString('zh-CN') : 'N/A';
        summaries.push({ time, content: `${evt.title || evt.event_id || ''} (${evt.country || ''})` });
      });
    }
    if (!summaries.length) {
      summaries.push({ time: new Date().toLocaleTimeString('zh-CN'), content: `数据源: ${data.data_mode || '未知'}` });
      summaries.push({ time: new Date().toLocaleTimeString('zh-CN'), content: `A股指数: ${Object.keys(data.a_shares || {}).length} 条` });
      summaries.push({ time: new Date().toLocaleTimeString('zh-CN'), content: `商品: ${Object.keys(data.commodities || {}).length} 条` });
    }

    this.elements.newsBanner.innerHTML = summaries.map(item => `
      <div class="news-item">
        <span class="news-time">${item.time}</span>
        <span class="news-content">${item.content}</span>
      </div>
    `).join('');
  }

  updateMarketStats(summary) {
    if (this.elements.advancingCount) {
      this.elements.advancingCount.textContent = summary.advancing || 0;
    }
    if (this.elements.decliningCount) {
      this.elements.decliningCount.textContent = summary.declining || 0;
    }
    if (this.elements.unchangedCount) {
      this.elements.unchangedCount.textContent = summary.unchanged || 0;
    }
  }

  updateMarquee(data) {
    if (!this.elements.marquee) return;

    const indices = data.a_shares || {};
    const marqueeItems = Object.entries(indices)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        return `${data.display_name || data.name}: ${this.formatNumber(data.last, 2)} (${this.formatChange(data.change_pct)}%)`;
      })
      .join('　　|　　');

    if (marqueeItems) {
      this.elements.marquee.innerHTML = `<span>${marqueeItems}</span>`;
    }
  }

  updateHeatmap(heatmap) {
    const container = document.getElementById('equity-heat');
    if (!container) return;

    if (!heatmap || heatmap.length === 0) {
      container.innerHTML = '<div class="loading-spinner">No heatmap data</div>';
      return;
    }

    const cells = heatmap.map((item) => {
      const cls = this.getChangeClass(item.pct_change);
      return `
        <div class="heat-cell ${cls}">
          <div class="heat-name">${item.name}</div>
          <div class="heat-change">${this.formatChange(item.pct_change)}%</div>
        </div>
      `;
    }).join('');

    container.innerHTML = cells;
  }

  updateCalendar(calendar) {
    const container = document.getElementById('calendar-list');
    if (!container) return;

    const events = calendar.events || [];
    if (events.length === 0) {
      container.innerHTML = '<div class="news-item"><span class="news-time">--</span><span class="news-content">No upcoming events</span></div>';
      return;
    }

    const items = events.slice(0, 5).map((event) => {
      const time = event.datetime ? new Date(event.datetime).toLocaleString('zh-CN') : "";
      return `
        <div class="news-item">
          <span class="news-time">${time}</span>
          <span class="news-content">${event.title || event.event_id || ''} (${event.country || ''})</span>
        </div>
      `;
    }).join('');

    container.innerHTML = items;
  }

  updateStatus(data) {
    const mode = data?.data_mode ?? data?.metadata?.data_mode ?? "mock";
    if (this.elements.statusDataMode) {
      this.elements.statusDataMode.textContent = mode;
    }

    const updatedAt = this.lastDataUpdate
      ? this.lastDataUpdate.toLocaleTimeString('zh-CN')
      : new Date().toLocaleTimeString('zh-CN');
    if (this.elements.statusLastUpdate) {
      this.elements.statusLastUpdate.textContent = updatedAt;
    }
    if (this.elements.headerDataMode) {
      this.elements.headerDataMode.textContent = `模式：${String(mode).toUpperCase()}`;
    }
    if (this.elements.headerLastUpdate) {
      this.elements.headerLastUpdate.textContent = `更新：${updatedAt}`;
    }

    if (this.elements.statusConnection) {
      this.elements.statusConnection.textContent = this.isConnected ? '已连接' : '连接中断';
      this.elements.statusConnection.style.color = this.isConnected ? '#4caf50' : '#f44336';
    }

    if (this.elements.statusFreshness) {
      const freshness = this.getDataFreshness();
      this.elements.statusFreshness.textContent = freshness.text;
      this.elements.statusFreshness.style.color = freshness.color;
    }
  }

  setConnectionStatus(connected) {
    this.isConnected = connected;
    this.updateConnectionStatus(connected);
  }

  markStale() {
    if (this.elements.statusLastUpdate) {
      this.elements.statusLastUpdate.textContent = "stale";
    }
    if (this.elements.headerLastUpdate) {
      this.elements.headerLastUpdate.textContent = "更新：暂停";
    }
  }

  // Utility methods
  getChangeClass(changePct) {
    if (!changePct && changePct !== 0) return 'unchanged';
    if (changePct > 0) return 'up';
    if (changePct < 0) return 'down';
    return 'unchanged';
  }

  formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
      return '--';
    }
    return Number(value).toFixed(decimals);
  }

  formatChange(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
      return '--';
    }
    const formatted = Number(value).toFixed(decimals);
    return value >= 0 ? `+${formatted}` : formatted;
  }

  getFXName(code) {
    const names = {
      'USDCNY.EX': 'USD/CNY',
      'EURCNY.EX': 'EUR/CNY',
      'HKDCNY.EX': 'HKD/CNY',
      'JPYCNY.EX': 'JPY/CNY',
      'USDCNH.FX': 'USD/CNH',
      'EURUSD.FX': 'EUR/USD',
      'USDJPY.FX': 'USD/JPY',
      'USDX.FX': 'DXY'
    };
    return names[code] || code;
  }

  getUSStockName(code) {
    const names = {
      'DJI.GI': '道琼斯',
      'SPX.GI': '标普500',
      'IXIC.GI': '纳斯达克',
      'AAPL.O': '苹果',
      'MSFT.O': '微软',
      'GOOGL.O': '谷歌',
      'TSLA.O': '特斯拉',
      'AMZN.O': '亚马逊'
    };
    return names[code] || code;
  }

  getRateName(code) {
    const names = {
      'M0000017.SH': '10年期国债',
      'M0000025.SH': '5年期国债',
      'M0000007.SH': '3年期国债',
      'M0000001.SH': '1年期国债',
      'UST10Y.GBM': '美10Y',
      'UST5Y.GBM': '美5Y',
      'UST2Y.GBM': '美2Y',
      'UST3M.GBM': '美3M',
      'TB10Y.WI': '中10Y',
      'TB5Y.WI': '中5Y',
      'TB3Y.WI': '中3Y',
      'TB1Y.WI': '中1Y',
      'LPR1Y.IR': 'LPR 1Y',
      'LPR5Y.IR': 'LPR 5Y'
    };
    return names[code] || code;
  }

  getCommodityName(code) {
    const names = {
      'GC.CMX': 'COMEX 黄金',
      'SI.CMX': 'COMEX 白银',
      'HG.CMX': 'COMEX 铜',
      'PL.NYM': 'NYMEX 铂金',
      'PA.NYM': 'NYMEX 钯金',
      'CL.NYM': 'WTI 原油',
      'COIL.BR': '布伦特原油',
      'NG.NYM': 'NYMEX 天然气',
      'ZC.CBT': 'CBOT 玉米',
      'ZS.CBT': 'CBOT 大豆',
      'KC.NYB': 'ICE 咖啡',
      'RB.SHF': '螺纹钢',
      'RB00.SHF': '螺纹钢',
      'I00.DCE': '铁矿石',
      'CU00.SHF': '沪铜',
      'AL00.SHF': '沪铝',
      'ZN00.SHF': '沪锌',
      'AU00.SHF': '沪金',
      'AG00.SHF': '沪银',
      'TA.CZC': 'PTA',
    };
    return names[code] || code;
  }

  getCommoditySector(code) {
    const sectors = {
      'GC.CMX': '贵金属',
      'SI.CMX': '贵金属',
      'PL.NYM': '贵金属',
      'PA.NYM': '贵金属',
      'HG.CMX': '基本金属',
      'ALI.CMX': '基本金属',
      'RB.SHF': '钢材',
      'RB00.SHF': '钢材',
      'J.DCE': '钢煤',
      'CL.NYM': '能源',
      'COIL.BR': '能源',
      'NG.NYM': '能源',
      'ZC.CBT': '农产品',
      'ZS.CBT': '农产品',
      'KC.NYB': '软商品',
      'TA.CZC': '化工',
      'SA.CZC': '化工',
      'S.CBT': '农产品',
      'C.CBT': '农产品',
      'W.CBT': '农产品',
      'LH.DCE': '畜牧',
    };
    return sectors[code] || '';
  }

  getDataFreshness() {
    if (!this.lastDataUpdate) {
      return { text: '等待数据', color: '#666' };
    }

    const now = new Date();
    const diff = (now - this.lastDataUpdate) / 1000;

    if (diff < 30) {
      return { text: '数据实时', color: '#4caf50' };
    } else if (diff < 60) {
      return { text: '数据较新', color: '#ff9800' };
    } else {
      return { text: '数据较旧', color: '#f44336' };
    }
  }

  // New methods for modern UI
  startClock() {
    const updateClock = () => {
      if (this.elements.currentTime) {
        const now = new Date();
        this.elements.currentTime.textContent = now.toLocaleTimeString('zh-CN', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      }
    };

    updateClock();
    setInterval(updateClock, 1000);
  }

  initializeSceneIndicators() {
    this.elements.sceneDots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        this.activeIndex = index;
        this.cycleScenes();
      });
    });
  }

  updateConnectionStatus(connected) {
    if (this.elements.connectionStatus) {
      const statusDot = this.elements.connectionStatus.querySelector('.status-dot');
      const statusText = this.elements.connectionStatus.querySelector('.status-text');

      if (statusDot && statusText) {
        if (connected) {
          statusDot.style.background = 'var(--market-up)';
          statusText.textContent = 'Live';
          statusText.style.color = 'var(--market-up)';
        } else {
          statusDot.style.background = 'var(--market-down)';
          statusText.textContent = 'Offline';
          statusText.style.color = 'var(--market-down)';
        }
      }
    }
  }

  // Cleanup
  destroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}

// Initialize wallboard when DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  console.log('Initializing Wind Market Wallboard...');
  window.wallboard = new WallboardController();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.wallboard) {
    window.wallboard.destroy();
  }
});
