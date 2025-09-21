# Docker Deployment

## Services
- `backend`: FastAPI application running under uv, exposes port 8000.
- `frontend`: Static nginx container serving `frontend/src` on port 4173 (host).
- `redis`: Redis 7 used for snapshot caching.

## Usage
```bash
cd deployment/docker
cp backend.env.example backend.env  # edit credentials and data mode
docker compose up --build
```

The wallboard frontend will be available at `http://localhost:4173` and the backend API at `http://localhost:8000`.

## Configuration
- Edit `backend.env` for runtime settings (data mode, Redis, credentials).
- To customise session schedules or refresh intervals, mount files from `config/defaults/` into the backend container or bake into an image layer as implementation evolves.

## Production Notes
- Replace nginx static server with CDN or kiosk-specific hosting as needed.
- Introduce authentication for `/config` endpoints before exposing beyond trusted networks.
- Consider multi-stage frontend build (e.g., Vite) once dynamic assets are added.
