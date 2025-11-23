/**
 * A股市场大屏显示控制器
 * 负责从后端获取数据并实时更新显示
 */

class ASharesWallboard {
  constructor() {
    this.apiBaseUrl = '/data';
    this.refreshInterval = 15000; // 15秒刷新间隔
    this.reconnectInterval = 5000; // 连接失败重试间隔
    this.isConnected = false;
    this.refreshTimer = null;
    this.lastUpdateTime = null;

    this.initializeElements();
    this.startDataRefresh();
    this.startClock();
  }

  initializeElements() {
    // Get DOM element references
    this.elements = {
      marquee: document.getElementById('marquee'),
      indicesGrid: document.getElementById('indices-grid'),
      fxGrid: document.getElementById('fx-grid'),
      commoditiesGrid: document.getElementById('commodities-grid'),
      usStocksGrid: document.getElementById('us-stocks-grid'),
      advancingCount: document.getElementById('advancing-count'),
      decliningCount: document.getElementById('declining-count'),
      unchangedCount: document.getElementById('unchanged-count'),
      dataSource: document.getElementById('data-source'),
      lastUpdate: document.getElementById('last-update'),
      connectionStatus: document.getElementById('connection-status'),
      currentTime: document.getElementById('current-time'),
      dataFreshness: document.getElementById('data-freshness'),
      connectionIndicator: document.getElementById('connection-indicator'),
      indicatorDot: document.querySelector('.status-dot'),
      indicatorText: document.querySelector('.status-text'),
      trendChart: document.getElementById('market-trend-chart'),
      marketStatusIndicator: document.getElementById('market-status-indicator'),
      systemHealthIndicator: document.getElementById('system-health-indicator'),
      marketSession: document.getElementById('market-session'),
      dataQualityIndicator: document.getElementById('data-quality-indicator')
    };

    // Store historical data for trend charts
    this.historicalData = {};

    // Initialize market session status
    this.updateMarketSession();
  }

  async startDataRefresh() {
    console.log('Starting A-shares wallboard data refresh...');

    // 立即加载一次数据
    await this.fetchAndUpdateData();

    // 设置定期刷新
    this.refreshTimer = setInterval(() => {
      this.fetchAndUpdateData();
    }, this.refreshInterval);
  }

  async fetchAndUpdateData() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/latest`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.updateDisplay(data);
      this.setConnectionStatus(true);
      this.lastUpdateTime = new Date();

    } catch (error) {
      console.error('Failed to fetch market data:', error);
      this.setConnectionStatus(false);

      // 重试连接
      setTimeout(() => {
        this.fetchAndUpdateData();
      }, this.reconnectInterval);
    }
  }

  updateDisplay(data) {
    this.updateIndices(data.a_shares || {});
    this.updateFX(data.fx || {});
    this.updateCommodities(data.commodities || {});
    this.updateUSStocks(data.us_stocks || {});
    this.updateMarketSummary(data.summary || {});
    this.updateMarquee(data);
    this.updateSystemStatus(data);
    this.updateTrendChart(data.a_shares || {});
  }

  updateIndices(indicesData) {
    if (!this.elements.indicesGrid) return;

    if (Object.keys(indicesData).length === 0) {
      this.elements.indicesGrid.innerHTML = '<div class="loading-spinner">No indices data available</div>';
      return;
    }

    const indicesHtml = Object.entries(indicesData)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        const changeSymbol = data.change >= 0 ? '+' : '';

        return `
          <div class="index-item ${changeClass}" data-code="${code}">
            <div class="index-header">
              <div class="index-name">${data.display_name || data.name || code}</div>
              <div class="index-code">${code}</div>
            </div>
            <div class="index-price">${this.formatNumber(data.last, 2)}</div>
            <div class="index-change">
              <span class="change-value ${changeClass}">
                ${changeSymbol}${this.formatNumber(data.change, 2)}
              </span>
              <span class="change-value ${changeClass}">
                (${changeSymbol}${this.formatNumber(data.change_pct, 2)}%)
              </span>
            </div>
          </div>
        `;
      })
      .join('');

    this.elements.indicesGrid.innerHTML = indicesHtml;
  }

  updateFX(fxData) {
    if (!this.elements.fxGrid) return;

    if (Object.keys(fxData).length === 0) {
      this.elements.fxGrid.innerHTML = '<div class="loading-spinner">No FX data available</div>';
      return;
    }

    const fxHtml = Object.entries(fxData)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        const changeSymbol = data.change >= 0 ? '+' : '';

        return `
          <div class="fx-item" data-code="${code}">
            <div class="item-name">${this.getFXName(code)}</div>
            <div class="item-value">
              <div class="item-price">${this.formatNumber(data.last, 4)}</div>
              <div class="item-change ${changeClass}">
                ${changeSymbol}${this.formatNumber(data.change_pct, 2)}%
              </div>
            </div>
          </div>
        `;
      })
      .join('');

    this.elements.fxGrid.innerHTML = fxHtml;
  }

  updateCommodities(commoditiesData) {
    if (!this.elements.commoditiesGrid) return;

    if (Object.keys(commoditiesData).length === 0) {
      this.elements.commoditiesGrid.innerHTML = '<div class="loading-spinner">No commodities data available</div>';
      return;
    }

    const commoditiesHtml = Object.entries(commoditiesData)
      .filter(([code, data]) => data && typeof data === 'object')
      .slice(0, 6) // Show top 6 commodities
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        const changeSymbol = (data.change_pct || 0) >= 0 ? '+' : '';

        return `
          <div class="commodity-item" data-code="${code}">
            <div class="item-name">${this.getCommodityName(code)}</div>
            <div class="item-value">
              <div class="item-price">${this.formatNumber(data.last, 0)}</div>
              <div class="item-change ${changeClass}">
                ${changeSymbol}${this.formatNumber(data.change_pct, 2)}%
              </div>
            </div>
          </div>
        `;
      })
      .join('');

    this.elements.commoditiesGrid.innerHTML = commoditiesHtml;
  }

  updateUSStocks(usStocksData) {
    if (!this.elements.usStocksGrid) return;

    if (Object.keys(usStocksData).length === 0) {
      this.elements.usStocksGrid.innerHTML = '<div class="loading-spinner">No US stocks data available</div>';
      return;
    }

    const usStocksHtml = Object.entries(usStocksData)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeClass = this.getChangeClass(data.change_pct);
        const changeSymbol = (data.change_pct || 0) >= 0 ? '+' : '';

        return `
          <div class="us-stock-item ${changeClass}" data-code="${code}">
            <div class="item-name">${this.getUSStockName(code)}</div>
            <div class="item-value">
              <div class="item-price">$${this.formatUSStockPrice(data.last)}</div>
              <div class="item-change ${changeClass}">
                ${changeSymbol}${this.formatNumber(data.change_pct, 2)}%
              </div>
            </div>
          </div>
        `;
      })
      .join('');

    this.elements.usStocksGrid.innerHTML = usStocksHtml;
  }

  updateMarketSummary(summaryData) {
    if (this.elements.advancingCount) {
      this.elements.advancingCount.textContent = summaryData.advancing || 0;
    }
    if (this.elements.decliningCount) {
      this.elements.decliningCount.textContent = summaryData.declining || 0;
    }
    if (this.elements.unchangedCount) {
      this.elements.unchangedCount.textContent = summaryData.unchanged || 0;
    }
  }

  updateMarquee(data) {
    if (!this.elements.marquee) return;

    const indices = data.a_shares || {};
    const marqueeItems = Object.entries(indices)
      .filter(([code, data]) => data && typeof data === 'object')
      .map(([code, data]) => {
        const changeSymbol = data.change >= 0 ? '+' : '';
        const changeClass = this.getChangeClass(data.change_pct);

        return `${data.display_name || data.name}: ${this.formatNumber(data.last, 2)} (${changeSymbol}${this.formatNumber(data.change_pct, 2)}%)`;
      })
      .join('　　|　　');

    if (marqueeItems) {
      this.elements.marquee.innerHTML = `<span>${marqueeItems}</span>`;
    }
  }

  updateSystemStatus(data) {
    const mode = data?.data_mode ?? data?.metadata?.data_mode ?? 'mock';
    if (this.elements.dataSource) {
      this.elements.dataSource.textContent = mode.toUpperCase();
    }

    if (this.elements.lastUpdate) {
      const label = this.lastUpdateTime
        ? this.formatTime(this.lastUpdateTime)
        : '--:--:--';
      this.elements.lastUpdate.textContent = label;
    }

    if (this.elements.connectionStatus) {
      this.elements.connectionStatus.textContent = this.isConnected ? 'Connected' : 'Disconnected';
      this.elements.connectionStatus.style.color = this.isConnected ? 'var(--market-up)' : 'var(--market-down)';
    }

    if (this.elements.dataFreshness) {
      const freshness = this.getDataFreshness();
      this.elements.dataFreshness.textContent = freshness.text;
      this.elements.dataFreshness.style.color = freshness.color;
    }

    // Update data quality indicator
    if (this.elements.dataQualityIndicator) {
      const quality = this.getDataQuality();
      this.elements.dataQualityIndicator.textContent = quality.text;
      this.elements.dataQualityIndicator.style.color = quality.color;
    }
  }

  setConnectionStatus(connected) {
    this.isConnected = connected;

    // Update connection indicator dot
    if (this.elements.indicatorDot) {
      this.elements.indicatorDot.style.background = connected
        ? 'var(--market-up)'
        : 'var(--market-down)';
    }

    // Update connection indicator text
    if (this.elements.indicatorText) {
      this.elements.indicatorText.textContent = connected ? 'Live' : 'Offline';
      this.elements.indicatorText.style.color = connected
        ? 'var(--market-up)'
        : 'var(--market-down)';
    }

    // Update system health indicator
    if (this.elements.systemHealthIndicator) {
      this.elements.systemHealthIndicator.style.background = connected
        ? 'var(--market-up)'
        : 'var(--market-down)';
    }

    // Update market status indicator
    if (this.elements.marketStatusIndicator) {
      this.elements.marketStatusIndicator.style.background = connected
        ? 'var(--market-up)'
        : 'var(--market-down)';
    }
  }

  startClock() {
    const updateClock = () => {
      if (this.elements.currentTime) {
        const now = new Date();
        this.elements.currentTime.textContent = this.formatTime(now);
      }
    };

    updateClock();
    setInterval(updateClock, 1000);
  }

  getChangeClass(changePct) {
    if (!changePct && changePct !== 0) return 'unchanged';
    if (changePct > 0) return 'up';
    if (changePct < 0) return 'down';
    return 'unchanged';
  }

  getFXName(code) {
    const names = {
      'USDCNY.EX': 'USD/CNY',
      'EURCNY.EX': 'EUR/CNY',
      'HKDCNY.EX': 'HKD/CNY',
      'JPYCNY.EX': 'JPY/CNY'
    };
    return names[code] || code;
  }

  getCommodityName(code) {
    const names = {
      'GC.CMX': 'COMEX 黄金',
      'SI.CMX': 'COMEX 白银',
      'HG.CMX': 'COMEX 铜',
      'CL.NYM': 'WTI 原油',
      'COIL.BR': '布伦特原油',
      'NG.NYM': 'NYMEX 天然气',
      'RB0000.SHF': '螺纹钢',
      'I0000.DCE': '铁矿石',
      'CU0000.SHF': '沪铜',
      'AL0000.SHF': '沪铝',
      'ZN0000.SHF': '沪锌',
      'AU0000.SHF': '沪金',
      'AG0000.SHF': '沪银'
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

  formatUSStockPrice(value) {
    if (value === null || value === undefined || isNaN(value)) {
      return '--';
    }

    // Format US stock prices - typically 2 decimal places
    if (value >= 1000) {
      return Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else {
      return Number(value).toFixed(2);
    }
  }

  formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
      return '--';
    }
    return Number(value).toFixed(decimals);
  }

  formatTime(date) {
    return date.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  getDataFreshness() {
    if (!this.lastUpdateTime) {
      return { text: 'Waiting for data', color: 'var(--text-muted)' };
    }

    const now = new Date();
    const diff = (now - this.lastUpdateTime) / 1000; // seconds

    if (diff < 30) {
      return { text: 'Real-time', color: 'var(--market-up)' };
    } else if (diff < 60) {
      return { text: 'Recent', color: 'var(--accent-warning)' };
    } else {
      return { text: 'Stale', color: 'var(--market-down)' };
    }
  }

  getDataQuality() {
    if (!this.lastUpdateTime) {
      return { text: 'Waiting', color: 'var(--text-muted)' };
    }

    const now = new Date();
    const diff = (now - this.lastUpdateTime) / 1000; // seconds

    if (diff < 15) {
      return { text: 'Real-time', color: 'var(--market-up)' };
    } else if (diff < 60) {
      return { text: 'Delayed', color: 'var(--accent-warning)' };
    } else {
      return { text: 'Stale', color: 'var(--market-down)' };
    }
  }

  updateMarketSession() {
    if (!this.elements.marketSession) return;

    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const timeInMinutes = hour * 60 + minute;

    // China market hours: 9:30-11:30, 13:00-15:00 (Beijing time)
    const morningOpen = 9 * 60 + 30;  // 9:30
    const morningClose = 11 * 60 + 30; // 11:30
    const afternoonOpen = 13 * 60;     // 13:00
    const afternoonClose = 15 * 60;    // 15:00

    let session = 'Closed';
    if ((timeInMinutes >= morningOpen && timeInMinutes <= morningClose) ||
        (timeInMinutes >= afternoonOpen && timeInMinutes <= afternoonClose)) {
      session = 'Market Open';
    } else if (timeInMinutes < morningOpen ||
               (timeInMinutes > morningClose && timeInMinutes < afternoonOpen)) {
      session = 'Pre-market';
    } else {
      session = 'After-hours';
    }

    this.elements.marketSession.textContent = session;
  }

  updateTrendChart(indicesData) {
    if (!this.elements.trendChart) return;

    // 保存主要指数的历史数据
    const mainIndices = ['000001.SH', '399001.SZ', '399006.SZ'];
    const now = new Date();

    // 初始化历史数据结构
    mainIndices.forEach(code => {
      if (!this.historicalData[code]) {
        this.historicalData[code] = [];
      }

      if (indicesData[code]) {
        this.historicalData[code].push({
          time: now.toLocaleTimeString('zh-CN', { hour12: false }),
          value: indicesData[code].last,
          change_pct: indicesData[code].change_pct
        });

        // 保持最近20个数据点
        if (this.historicalData[code].length > 20) {
          this.historicalData[code] = this.historicalData[code].slice(-20);
        }
      }
    });

    // 创建简单的趋势图显示
    const chartHtml = this.createSimpleTrendChart(mainIndices, indicesData);
    this.elements.trendChart.innerHTML = chartHtml;
  }

  createSimpleTrendChart(indices, currentData) {
    return `
      <div class="trend-chart-container">
        <h4>主要指数实时趋势</h4>
        <div class="chart-legend">
          ${indices.map(code => {
            const data = currentData[code];
            if (!data) return '';
            const changeClass = this.getChangeClass(data.change_pct);
            return `
              <div class="legend-item ${changeClass}">
                <span class="legend-dot"></span>
                <span class="legend-name">${this.getIndexName(code)}</span>
                <span class="legend-value">${this.formatNumber(data.last, 2)}</span>
                <span class="legend-change">${data.change_pct >= 0 ? '+' : ''}${this.formatNumber(data.change_pct, 2)}%</span>
              </div>
            `;
          }).join('')}
        </div>
        <div class="simple-chart">
          ${indices.map(code => {
            const history = this.historicalData[code] || [];
            if (history.length === 0) return '';

            return `
              <div class="chart-line" data-code="${code}">
                <div class="line-header">${this.getIndexName(code)}</div>
                <div class="line-bars">
                  ${history.slice(-10).map((point, index) => {
                    const changeClass = this.getChangeClass(point.change_pct);
                    const height = Math.max(3, Math.abs(point.change_pct) * 5 + 10);
                    return `
                      <div class="bar ${changeClass}"
                           style="height: ${height}px"
                           title="${point.time}: ${this.formatNumber(point.value, 2)} (${point.change_pct >= 0 ? '+' : ''}${this.formatNumber(point.change_pct, 2)}%)">
                      </div>
                    `;
                  }).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
        <div class="chart-tip">点击指数查看详细信息 • 显示最近${Math.max(...indices.map(code => this.historicalData[code]?.length || 0))}个数据点</div>
      </div>
    `;
  }

  getIndexName(code) {
    const names = {
      '000001.SH': '上证综指',
      '399001.SZ': '深证成指',
      '399006.SZ': '创业板指',
      '000300.SH': '沪深300',
      '000905.SH': '中证500'
    };
    return names[code] || code;
  }

  // Cleanup method
  destroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing A-shares modern dashboard...');
  window.wallboard = new ASharesWallboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.wallboard) {
    window.wallboard.destroy();
  }
});
