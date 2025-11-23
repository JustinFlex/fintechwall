# Wind Market Wallboard – Testing Standards & Process

## 1. Purpose & Scope
Establish a repeatable testing framework that guarantees both Wind Edition and Open Edition of the wallboard deliver accurate, timely, and reliable market insights. The plan covers backend services (Python), front-end carousel (HTML/CSS/JavaScript), data pipelines, and kiosk deployment workflows. All test activities must ensure parity between editions, with emphasis on data integrity and resilience.

## 2. Testing Objectives
- Validate functional requirements from the PRD across all scenes and carousel behaviours.
- Assure data correctness, freshness, and fallback logic for both data provider stacks.
- Confirm front-end rendering, accessibility, and kiosk usability at 4K resolution.
- Demonstrate system stability under continuous 72-hour operation with live data streams.
- Provide auditable evidence that release candidates meet acceptance criteria before deployment.

## 3. Test Environments
| Environment | Purpose | Data Sources | Notes |
| --- | --- | --- | --- |
| **DEV** | Rapid iteration, unit/integration tests | Mock providers, recorded fixtures | Automatically provisioned via Docker Compose |
| **QA (Wind)** | End-to-end validation using Wind data | Live WindPy (sandbox credentials) | Restricted to internal network |
| **QA (Open)** | End-to-end validation using open/free APIs | Public APIs with rate limits | Use throttling and caching to avoid bans |
| **Pilot** | Dress rehearsal on kiosk hardware | Same as production | 72-hour burn-in test |

## 4. Test Categories
### 4.1 Unit Tests
- **Backend**: Pytest with coverage on provider adapters, data normalisers, schedulers, WebSocket managers.
- **Front-End**: Jest/Vitest for utility modules (data formatting, scheduling).
- Success criteria: ≥ 85% line coverage on critical modules (providers, schedulers, carousel timing).

### 4.2 Provider Contract Tests
- Validate schema compliance for both Wind and Open providers using mocked responses and live sanity checks.
- Ensure each provider returns mandatory fields (`code`, `label`, `value`, `timestamp`, `source`).
- Use JSON Schema or Pydantic-based contract tests executed in CI.

### 4.3 Data Quality & Freshness
- Automated validation (Great Expectations or custom checks) for:
  - Timestamp recency vs SLA per asset class.
  - Numerical sanity (e.g., price > 0, percentage change within ±50% intraday unless flag raised).
  - Cross-field consistency (e.g., stablecoin dominance sums to ≤ 100%).
- Alert triggered when consecutive failures exceed threshold.

### 4.4 Integration Tests
- Exercise ingestion workflow end-to-end using dockerised Redis.
- Use Recorded fixtures (VCR.py/Betamax) to simulate API responses for deterministic CI runs.
- Verify fallback chain (primary failure → secondary success → cache update) in both editions.

### 4.5 System & Functional Tests
- Scenario-based tests ensuring carousel rotation, session weighting, stale indicators, and risk alerts behave per PRD.
- Use Playwright to script kiosk viewport (3840×2160) and assert DOM states per scene.

### 4.6 UI/UX & Accessibility Tests
- Visual regression using Playwright screenshot comparison or BackstopJS for key scenes.
- Accessibility audit via Axe-core (contrast, ARIA roles, keyboard navigation even though kiosk is passive).
- Verify font sizes and colour palette meet design specs.

### 4.7 Performance & Load Tests
- Backend throughput tests with Locust/k6 simulating concurrent kiosk connections (baseline 5 clients, headroom 20).
- Measure WebSocket latency (<1 s) and REST response time (<500 ms) under load.
- Front-end rendering performance measured with Lighthouse (simulate 4K display, ensure no long tasks > 200 ms).

### 4.8 Resilience & Failover Tests
- Chaos scenarios: Wind outage, open API rate limit, Redis restart, network drop on kiosk.
- Validate fallback logic, stale badge behaviour, and auto recovery.
- 72-hour soak test with automated monitors to catch memory leaks or timer drift.

### 4.9 Security & Compliance Checks
- Verify HTTPS enforcement, CORS restrictions, and sanitisation of news headlines (strip HTML/JS).
- Static analysis (Bandit, Ruff) and dependency vulnerability scans (pip-audit, npm audit for static assets).

### 4.10 Regression Tests
- Automated suite triggered on every merge to main; includes unit, integration, contract, and key Playwright scripts.
- Release candidate must run full regression on QA environments for both editions.

### 4.11 User Acceptance Testing (UAT)
- Conduct structured walkthrough with pilot stakeholders using checklist derived from PRD acceptance criteria.
- Record sign-off and capture feedback for backlog grooming.

## 5. Test Data Management
- **Wind Edition**: Use dedicated Wind sandbox account; log API usage to ensure quotas respected.
- **Open Edition**: Cache sample payloads to reduce live calls; mask API keys in fixtures.
- Store deterministic fixtures in version control for repeatable unit/integration tests.
- For sensitive data (if any), apply anonymisation or use synthetic substitutes.

## 6. Automation & Tooling
| Area | Tooling | Notes |
| --- | --- | --- |
| Unit/Integration | Pytest, pytest-asyncio, VCR.py | Run in CI with coverage reports |
| Schema Validation | Pydantic models, jsonschema | Enforce canonical payload structure |
| Front-End Tests | Playwright, Vitest | Headless and headed modes at 4K |
| Visual Regression | Playwright traces or BackstopJS | Baseline images stored per edition |
| Accessibility | Axe-core CLI, Lighthouse | Automate in CI nightly |
| Performance | k6 or Locust | Script scenarios for REST & WebSocket |
| Monitoring | Prometheus + Grafana (QA/Pilot) | Capture metrics during soak tests |
| Static Analysis | Ruff, Bandit, ESLint | Enforced pre-commit and in CI |

## 7. Testing Process
1. **Planning**
   - Define test plan per milestone, map requirements to test cases, identify risks.
   - Update traceability matrix linking PRD features to test coverage.
2. **Preparation**
   - Provision environment (Docker Compose for DEV, sandbox credentials for QA).
   - Generate or refresh fixtures; configure Playwright baselines.
3. **Execution**
   - Run automated suites via CI on each pull request.
   - Perform manual exploratory tests on QA after major features (focus on layout and kiosk feel).
4. **Bug Management**
   - Log defects in tracker (severity, edition, scene, test reference).
   - Triage daily; critical issues block release until resolved.
5. **Reporting**
   - Publish CI dashboards (coverage, pass/fail) and weekly QA summary.
   - For pilot runs, capture uptime, data freshness metrics, and user feedback.
6. **Release Readiness**
   - Verify entry criteria: all priority test cases executed, no open Sev1/Sev2 issues, regression passed on both editions.
   - Exit criteria: UAT sign-off, soak test success, documentation updated.

## 8. Roles & Responsibilities
| Role | Responsibilities |
| --- | --- |
| QA Lead | Maintain test strategy, coordinate schedules, approve release readiness |
| Backend Engineer | Implement provider/unit tests, fix ingestion defects |
| Front-End Engineer | Maintain Playwright suites, visual baselines |
| DevOps | Manage QA environments, monitor soak tests |
| Product Owner | Review UAT outcomes, approve acceptance criteria |

## 9. Testing Schedule Alignment
- **Phase 1 (Foundation)**: Unit & contract tests for Scene A providers; CI pipeline baseline.
- **Phase 2 (Data Coverage)**: Integration tests for Scenes B–E; initial Playwright scripts.
- **Phase 3 (Frontend MVP)**: UI regression & accessibility smoke tests.
- **Phase 4 (Visual Enhancements)**: Update visual baselines; run performance benchmarks on new charts.
- **Phase 5 (Scheduling/Theming)**: Scenario tests for session weighting and dark mode.
- **Phase 6 (Resilience)**: Execute chaos and 72-hour soak tests in QA.
- **Phase 7 (Packaging)**: Final regression, UAT, and pilot validation.

## 10. Quality Metrics
- Automated test pass rate (build-level).
- Code coverage percentages (backend, frontend).
- Data freshness compliance (% within SLA by asset class).
- Defect density (issues per feature) and mean time to resolution.
- Uptime during pilot burn-in.

## 11. Deliverables
- Master test plan document (living, stored in `docs/`).
- Test case repository or spreadsheet linked to features.
- Automated test suites in version control with CI badges.
- QA run reports per milestone, including defects and metrics.
- Final release test summary with sign-off records.

## 12. Review & Continuous Improvement
- Retrospective after each release to refine test cases, tooling, and automation gaps.
- Update fixtures and baselines quarterly or when significant market events change visual expectations.
- Track flaky tests; remediate within one sprint.

