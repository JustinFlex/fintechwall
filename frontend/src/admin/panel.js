const API_BASE = window.__WALLBOARD_API__ ?? "http://localhost:8000";

async function fetchConfig() {
  try {
    const response = await fetch(`${API_BASE}/config`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const config = await response.json();
    hydrate(config);
  } catch (error) {
    console.warn("Falling back to defaults", error);
  }
}

function hydrate(config) {
  if (config?.data_mode) {
    document.getElementById("data-mode").value = config.data_mode;
  }
}

async function persist() {
  const button = document.getElementById("save-config");
  const status = document.getElementById("save-status");
  button.disabled = true;
  status.textContent = "Saving…";
  try {
    const payload = {
      data_mode: document.getElementById("data-mode").value,
    };
    const response = await fetch(`${API_BASE}/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    status.textContent = "Saved";
  } catch (error) {
    console.error("Failed to save configuration", error);
    status.textContent = "Failed";
  } finally {
    button.disabled = false;
  }
}

function init() {
  fetchConfig();
  document.getElementById("save-config").addEventListener("click", persist);
}

document.addEventListener("DOMContentLoaded", init);
