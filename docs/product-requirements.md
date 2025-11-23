# Wind Market Wallboard – Product Requirements Document

## 1. Executive Summary
Provide a 1-minute, multi-scene visual wallboard that enables viewers to grasp global market conditions at a glance. The product targets trading floors, classrooms, and briefing rooms that need passive, continuously refreshed situational awareness. Two data editions are supported:
- **Wind Edition**: Relies on WindPy/WAPI for institutional-grade data.
- **Open Edition**: Uses only non-commercial, open/free APIs to support environments without Wind access.

Both variants share identical user experience, layout, and behaviour while differing only in data sources and integration credentials. The stack uses a Python backend for data aggregation and a standards-based HTML/CSS/JavaScript front-end running in kiosk mode.

## 2. Goals & Non-Goals
### 2.1 Goals
- Deliver actionable, visually rich market intelligence within 60 seconds of passive viewing.
- Support automated carousel of five scenes (A–E) with configurable dwell times and session-aware weighting.
- Provide reliable data coverage across equities, commodities, FX, rates, crypto, and macro news for global markets.
- Offer consistent experience across both Wind and Open editions with minimal operator intervention.
- Run reliably on 55–65″ 4K displays with auto-start, reconnect, and offline caching.

### 2.2 Non-Goals
- Detailed analytics, chart drill-down, or user-driven interaction (product is “lean-back” display only).
- Portfolio management, trading execution, or alerting workflows.
- Mobile or desktop interactive client beyond kiosk display.

## 3. Personas & Use Cases
| Persona | Needs | Pain Points Addressed |
| --- | --- | --- |
| Trading Desk Lead | Rapid morning briefing, cross-asset awareness | Reduces manual tab switching and summarising |
| Economics Lecturer | Visual teaching aid for macro/rates discussions | Provides curated, reliable data feed |
| Operations Manager | Monitor market state during shifts | Single glance shows global status and risk alerts |

### Key Use Cases
1. **Opening Briefing**: Prior to Asia open, presenter references wallboard to confirm overnight moves, FX levels, and macro events.
2. **Midday Monitoring**: Desk uses Scene B heatmap and Scene C rates to adjust intraday risk posture.
3. **Evening Crypto Watch**: Overnight team relies on Scene D metrics for funding rates and open interest shifts.

## 4. User Scenarios & Journey
1. **Auto-Start**: Display boots, kiosk browser launches wallboard URL, automatic authentication (if needed) and scene carousel begins.
2. **Passive Viewing**: Audience watches looping scenes; marquee ticker and hero cards emphasise key changes; stale data flagged automatically.
3. **Session Shift**: At 20:00 SGT the carousel reprioritises US-focused views without manual input.
4. **Source Failover**: If Wind becomes unreachable, system switches to fallback data; viewer sees timestamp and subtle “stale” indicator until recovery.

## 5. Functional Requirements
### 5.1 Carousel & Scheduling
- Must cycle through Scenes A–E with configurable dwell time (default 20–45 seconds per scene, total loop <= 60 seconds).
- Must support session-based weighting (Asia, Europe, US, Overnight) altering dwell ratios via configuration file.
- Must expose manual override API (protected) for operators to pin a scene if required.

### 5.2 Scene Requirements
- **Scene A – Global Overview**: Display required indices, commodities, FX pairs, rates, crypto snapshot, and exchange status indicators.
- **Scene B – Equity Heat**: Show regional heatmap, top movers list with liquidity filters, implied vol panel (VIX, VXN, 1M/3M curve).
- **Scene C – Macro & Rates**: Render yield curves with week-over-week comparison, Fed Funds probabilities, SOFR/SORA tiles, and economic calendar with countdown.
- **Scene D – Crypto Depth**: Provide spot metrics, annualised volatility, funding rates, aggregated open interest, stablecoin flows, and on-chain activity metric.
- **Scene E – News Banner (optional)**: Show rolling headlines or event countdowns; highlight risk flags (e.g., VIX above threshold, 2s10s inversion).

### 5.3 Data Freshness & Indicators
- Each data card must display last updated timestamp (relative) and source edition metadata.
- System must differentiate fresh vs stale content (e.g., subtle dimming or “last updated” label after SLA breach).

### 5.4 Accessibility & Visual Requirements
- Use blue/orange palette and ▲▼ glyphs for colour-blind accessibility.
- Maintain minimum 60–80 px for hero numerals; ensure WCAG AA contrast ratios.
- Provide auto dark mode after configurable time.

### 5.5 Device & Deployment
- Must run in Chromium kiosk (Linux or Windows) at 4K resolution.
- Must auto-reconnect on network glitches and resume carousel from last scene state.
- Must cache last payload locally to display during brief outages with timestamp label.

## 6. Data Requirements
- **Editions**: Configuration must allow selecting Wind or Open data mode at deployment time.
- **Coverage**: Mandatory metrics listed per scene; fallback metrics defined when primary unavailable.
- **Latency**: Target <10s for high-frequency feeds (FX/crypto), <5 min for macro/calendar updates.
- **Quality**: Validate incoming data for outliers; ensure consistent units and currency labelling.

## 7. Success Metrics
- Carousel uptime ≥ 99% during trading hours.
- Data freshness SLA meeting targets: ≥ 95% of FX/crypto updates within 15s, ≥ 95% of rates updates within 5 min.
- User satisfaction (qualitative): stakeholders report improved briefing efficiency in pilot surveys.
- Minimal manual interventions (<2 per week) for data source issues after launch.

## 8. Rollout Plan
1. **Pilot**: Deploy Wind Edition to internal desk with manual monitoring.
2. **Feedback Loop**: Gather qualitative feedback, adjust visuals and scheduling profiles.
3. **Open Edition Release**: Launch Wind-free variant for partners without Wind access.
4. **General Availability**: Provide deployment guide, kiosk scripts, and admin training.

## 9. Dependencies
- Wind Edition depends on Wind terminal credentials and network connectivity to Wind servers.
- Open Edition depends on availability of public APIs (rate limits, key management where applicable).
- Requires kiosk hardware capable of 4K output and stable network connection.

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Wind licence limitations | Legal/contractual issues | Confirm redistribution terms with compliance before deployment |
| Open API rate limits/outages | Data freshness degradation | Implement caching, fallback providers, and alerts |
| Visual overload on large display | Reduced readability | Enforce layout grid, typography standards, and limited clutter |
| Session logic misconfiguration | Wrong scene emphasis | Provide tested defaults and admin tooling to validate schedules |
| Crypto WebSocket disconnects | Missing funding/OI data | Implement retry/backoff and fallback to last known values |

## 11. Acceptance Criteria
- Carousel operates for 72-hour continuous run without manual reset.
- Switching between Wind and Open editions requires only configuration change and restart.
- Scenes display all mandatory metrics with correct labelling and refresh cadences.
- Kiosk deployment starts automatically on device boot and recovers from network interruption within 30 seconds.
- Documentation delivered: development guide, PRD, technical architecture, deployment checklist.

## 12. Appendix
- Scene content tables (see Development Guide).
- API attribution requirements and SLA notes per provider.
- Glossary: OI (Open Interest), SLA (Service Level Agreement), SORA/SOFR, 2s10s inversion.
