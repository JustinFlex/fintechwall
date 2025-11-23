const DEFAULT_API_BASE = "http://localhost:8000";

export const API_BASE = window.__WALLBOARD_API__ ?? DEFAULT_API_BASE;

export async function fetchLatestSnapshot() {
  const res = await fetch(`${API_BASE}/data/latest`);
  if (!res.ok) {
    throw new Error(`Failed to fetch latest snapshot: HTTP ${res.status}`);
  }
  return res.json();
}
