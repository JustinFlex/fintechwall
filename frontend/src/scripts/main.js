const API_BASE = window.__WALLBOARD_API__ ?? "http://localhost:8000";
const CAROUSEL_INTERVAL = 25_000; // default dwell time in ms
const scenes = ["scene-a", "scene-b", "scene-c", "scene-d", "scene-e"];

let activeIndex = 0;
let intervalId = null;

function cycleScenes() {
  const visibleScene = scenes[activeIndex % scenes.length];
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("panel--active", panel.id === visibleScene);
  });
  activeIndex += 1;
}

async function fetchSnapshot() {
  try {
    const response = await fetch(`${API_BASE}/data/snapshot`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    updateStatus(payload);
  } catch (error) {
    console.error("Failed to fetch snapshot", error);
    markStale();
  }
}

function updateStatus(payload) {
  const mode = payload?.metadata?.data_mode ?? "n/a";
  const updatedAt = new Date().toLocaleTimeString();
  document.getElementById("status-data-mode").textContent = mode;
  document.getElementById("status-last-update").textContent = updatedAt;
}

function markStale() {
  document.getElementById("status-last-update").textContent = "stale";
}

function startCarousel() {
  cycleScenes();
  intervalId = window.setInterval(cycleScenes, CAROUSEL_INTERVAL);
}

function init() {
  startCarousel();
  fetchSnapshot();
  window.setInterval(fetchSnapshot, 30_000);
}

window.addEventListener("DOMContentLoaded", init);
