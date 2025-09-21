# Wind Market Wallboard Frontend

HTML/CSS/JavaScript kiosk client for the wallboard. The layout follows the three-column plus marquee grid described in the design docs and is optimised for 16:9 4K displays.

## Development
- Entry file: `src/index.html`
- Styles: `src/styles/main.css`
- Behaviour: `src/scripts/main.js`
- Admin console: `src/admin/index.html` for configuring data sources and refresh overrides.

To preview locally, serve `src/` via a static server (e.g. `python -m http.server`) and set `window.__WALLBOARD_API__` in the console to the backend URL if different from `http://localhost:8000`.
