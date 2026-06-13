const toggleBtn = document.getElementById("toggle-btn");
const connectionStatus = document.getElementById("connection-status");
const statusBar = document.getElementById("status-bar");
const downloadsList = document.getElementById("downloads-list");

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + units[i];
}

function formatSpeed(bytesPerSec) {
  return formatBytes(bytesPerSec) + "/s";
}

async function checkConnection() {
  const result = await browser.runtime.sendMessage({ type: "ping" });
  if (result && result.status === "ok") {
    connectionStatus.textContent = "Connected - Cove v" + result.version;
    statusBar.className = "status-bar connected";
  } else {
    connectionStatus.textContent = "Not connected to Cove";
    statusBar.className = "status-bar error";
  }
}

async function loadSettings() {
  const s = await browser.runtime.sendMessage({ type: "getSettings" });
  toggleBtn.textContent = s.enabled ? "ON" : "OFF";
  toggleBtn.dataset.enabled = s.enabled;
}

toggleBtn.addEventListener("click", async () => {
  const s = await browser.runtime.sendMessage({ type: "getSettings" });
  s.enabled = !s.enabled;
  await browser.runtime.sendMessage({ type: "saveSettings", settings: s });
  toggleBtn.textContent = s.enabled ? "ON" : "OFF";
  toggleBtn.dataset.enabled = s.enabled;
});

document.getElementById("open-options").addEventListener("click", () => {
  browser.runtime.openOptionsPage();
});

function renderDownloads(downloads) {
  if (!downloads || downloads.length === 0) {
    downloadsList.innerHTML = '<div class="empty-state">No active downloads</div>';
    return;
  }

  downloadsList.innerHTML = downloads
    .map((dl) => {
      const files = dl.files || [];
      const filename = files[0]?.path?.split("/").pop() || "Unknown";
      const total = parseInt(dl.totalLength || 0);
      const completed = parseInt(dl.completedLength || 0);
      const speed = parseInt(dl.downloadSpeed || 0);
      const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

      return `
        <div class="download-item">
          <div class="download-filename" title="${filename}">${filename}</div>
          <div class="download-progress">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${pct}%"></div>
            </div>
            <span class="download-speed">${formatSpeed(speed)}</span>
          </div>
          <div class="download-meta">
            <span>${pct}% - ${formatBytes(completed)} / ${formatBytes(total)}</span>
          </div>
        </div>
      `;
    })
    .join("");
}

async function refreshDownloads() {
  const result = await browser.runtime.sendMessage({ type: "getStatus" });
  if (result && result.status === "ok") {
    renderDownloads(result.downloads);
  }
}

checkConnection();
loadSettings();
refreshDownloads();

setInterval(refreshDownloads, 2000);
