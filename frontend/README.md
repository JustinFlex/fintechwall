# Wind Market Wallboard Frontend

HTML/CSS/JavaScript kiosk client for the wallboard. The layout follows the three-column plus marquee grid described in the design docs and is optimised for 16:9 4K displays.

## Quick preview (minimal runnable pages)
- Preferred modern page: `src/wallboard.html`. Basic placeholder version: `src/index.html`.
- Legacy design migrated from `FrontendDesign`: `src/rolling-screen.html` (multi-scene auto rotation referencing the mock API).
- Start a static server, e.g.:
  ```bash
  cd frontend
  python -m http.server 8001 -d src
  # Open http://localhost:8001/wallboard.html
  ```
- If the backend runs elsewhere, set `window.__WALLBOARD_API__ = "http://localhost:8000"` in DevTools console.

## Structure
- Entry files: `src/wallboard.html` (modern), `src/index.html` (basic), `src/rolling-screen.html` (design-porting)
- Styles: `src/styles/main.css`, `src/styles/wallboard-modern.css`, `src/styles/a-shares.css`, `src/styles/rolling-screen.css`, etc.
- Behaviour: `src/scripts/main.js`, `src/scripts/wallboard.js`, `src/scripts/a-shares.js`, `src/scripts/rolling-screen.js`
- Admin console: `src/admin/index.html` for configuring data sources and refresh overrides.
