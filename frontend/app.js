/**
 * QR-Chaff Frontend — app.js
 * Served by FastAPI at http://localhost:8000
 * Uses relative URLs — no CORS issues, single origin.
 */

// Use relative URL since frontend is served by FastAPI itself
const API = window.location.origin;
let accessToken = localStorage.getItem("access_token") || null;
let currentUser = JSON.parse(localStorage.getItem("current_user") || "null");
let activeSessionId = null;
let ws = null;

// Chart instances
let trafficChart = null;
let entropyChart = null;

// Live data buffers
const MAX_POINTS = 80;
let trafficData = { real: [], dummy: [], labels: [] };
let entropyData = { values: [], labels: [] };
let pathCounts = [0, 0, 0];
let packetIndex = 0;

// ── Helpers ────────────────────────────────────────────────────────────────
function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${accessToken}`,
  };
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: authHeaders(),
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.remove("hidden");
}

function clearError(id) {
  const el = document.getElementById(id);
  el.textContent = "";
  el.classList.add("hidden");
}

// ── Auth ───────────────────────────────────────────────────────────────────
function updateUI() {
  const loggedIn = !!accessToken;
  document.getElementById("authWall").classList.toggle("hidden", loggedIn);
  document.getElementById("dashboard").classList.toggle("hidden", !loggedIn);
  document.getElementById("navAuth").classList.toggle("hidden", loggedIn);
  document.getElementById("navUser").classList.toggle("hidden", !loggedIn);
  if (currentUser) {
    document.getElementById("usernameDisplay").textContent = `👤 ${currentUser.username}`;
  }
  if (loggedIn) {
    loadSessions();
    loadKeys();
    checkHealth();
  }
}

async function checkHealth() {
  try {
    const data = await fetch(`${API}/api/health`).then(r => r.json());
    const badge = document.getElementById("pqBadge");
    badge.textContent = `PQ: ${data.pq_mode}`;
    badge.style.color = data.pq_mode.includes("real") ? "#34d399" : "#f59e0b";
  } catch (e) { /* backend not ready yet */ }
}

async function doLogin(username, password) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  accessToken = data.access_token;
  localStorage.setItem("access_token", accessToken);
  currentUser = { username };
  localStorage.setItem("current_user", JSON.stringify(currentUser));
}

async function doRegister(username, email, password) {
  const res = await fetch(`${API}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Registration failed");
  return data;
}

function doLogout() {
  accessToken = null;
  currentUser = null;
  activeSessionId = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("current_user");
  if (ws) { ws.close(); ws = null; }
  resetCharts();
  updateUI();
}

// ── Sessions ───────────────────────────────────────────────────────────────
async function loadSessions() {
  try {
    const sessions = await apiFetch("/api/sessions");
    renderSessionList(sessions);
  } catch (e) { console.warn("Could not load sessions:", e.message); }
}

function renderSessionList(sessions) {
  const el = document.getElementById("sessionList");
  if (!sessions || sessions.length === 0) {
    el.innerHTML = '<div class="empty-state">No sessions yet</div>';
    return;
  }
  el.innerHTML = sessions.map(s => `
    <div class="session-item ${s.id === activeSessionId ? 'active' : ''}"
         onclick="selectSession('${s.id}', '${s.session_name}')">
      <div class="session-dot ${s.status === 'active' ? 'active' : ''}"></div>
      <span class="session-name">${s.session_name}</span>
      <span class="session-status">${s.status}</span>
    </div>
  `).join("");
}

async function selectSession(id, name) {
  activeSessionId = id;
  document.getElementById("startEngineBtn").disabled = false;
  document.getElementById("stopEngineBtn").disabled = false;
  document.getElementById("sendDataBtn").disabled = false;
  loadSessions();
  toast(`Selected session: ${name}`);

  try {
    const statusData = await apiFetch(`/api/engine/status/${id}`);
    const isRunning = statusData && statusData.status === "running";
    updateEngineIndicator(isRunning);
    if (isRunning) {
      connectWebSocket(id);
    } else {
      if (ws) { ws.close(); ws = null; }
    }
  } catch (e) {
    updateEngineIndicator(false);
    if (ws) { ws.close(); ws = null; }
  }
}

async function createSession() {
  const name = document.getElementById("sessionName").value.trim() || undefined;
  try {
    const s = await apiFetch("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ session_name: name }),
    });
    toast(`Session "${s.session_name}" created`);
    selectSession(s.id, s.session_name);
    await loadSessions();
  } catch (e) { toast(e.message, "error"); }
}

// ── Engine ─────────────────────────────────────────────────────────────────
async function startEngine() {
  if (!activeSessionId) { toast("Select a session first", "error"); return; }
  try {
    await apiFetch("/api/engine/start", {
      method: "POST",
      body: JSON.stringify({ session_id: activeSessionId }),
    });
    toast("Engine started! 🚀");
    updateEngineIndicator(true);
    connectWebSocket(activeSessionId);
    await loadSessions();
  } catch (e) { toast(e.message, "error"); }
}

async function stopEngine() {
  if (!activeSessionId) return;
  try {
    await apiFetch(`/api/engine/stop?session_id=${activeSessionId}`, { method: "POST" });
    toast("Engine stopped.");
    updateEngineIndicator(false);
    if (ws) { ws.close(); ws = null; }
    await loadSessions();
  } catch (e) { toast(e.message, "error"); }
}

async function sendData() {
  if (!activeSessionId) { toast("Select a session first", "error"); return; }
  const msg = document.getElementById("sendMessage").value.trim();
  if (!msg) { toast("Enter a message", "error"); return; }
  try {
    await apiFetch("/api/engine/send", {
      method: "POST",
      body: JSON.stringify({ session_id: activeSessionId, message: msg }),
    });
    toast(`✉️ Sent: "${msg.substring(0, 30)}..." (AES-256-GCM encrypted)`);
    document.getElementById("sendMessage").value = "";
  } catch (e) { toast(e.message, "error"); }
}

function updateEngineIndicator(running) {
  const dot = document.getElementById("engineDot");
  const txt = document.getElementById("engineStatusText");
  dot.className = `dot ${running ? "running" : ""}`;
  txt.textContent = `Engine: ${running ? "Running" : "Offline"}`;
}

// ── WebSocket ──────────────────────────────────────────────────────────────
function connectWebSocket(sessionId) {
  if (ws) ws.close();
  // Use same host as the page (works whether HTTP or HTTPS)
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${wsProtocol}//${window.location.host}/api/engine/stream/${sessionId}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => console.log("WebSocket connected");
  ws.onerror = (e) => console.warn("WebSocket error", e);
  ws.onclose = () => { ws = null; updateEngineIndicator(false); };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "packet") handlePacket(msg.data);
    if (msg.type === "stats") updateStats(msg.data);
  };

  // Keepalive ping
  setInterval(() => { if (ws && ws.readyState === 1) ws.send("ping"); }, 25000);
}

function handlePacket(data) {
  packetIndex++;
  const label = packetIndex.toString();

  // Traffic chart
  trafficData.labels.push(label);
  if (data.is_dummy) {
    trafficData.dummy.push(data.size);
    trafficData.real.push(null);
  } else {
    trafficData.real.push(data.size);
    trafficData.dummy.push(null);
  }
  if (trafficData.labels.length > MAX_POINTS) {
    trafficData.labels.shift();
    trafficData.real.shift();
    trafficData.dummy.shift();
  }
  updateTrafficChart();

  // Entropy chart
  entropyData.labels.push(label);
  entropyData.values.push(data.entropy);
  if (entropyData.labels.length > MAX_POINTS) {
    entropyData.labels.shift();
    entropyData.values.shift();
  }
  updateEntropyChart();

  // Multipath
  const p = data.path_id || 0;
  if (p >= 0 && p <= 2) pathCounts[p]++;
  updateMultipath();

  // Stats panel
  const total = trafficData.real.filter(v => v !== null).length + trafficData.dummy.filter(v => v !== null).length;
  document.getElementById("statTotal").textContent = packetIndex;
  document.getElementById("statReal").textContent = trafficData.real.filter(v => v !== null).length;
  document.getElementById("statDummy").textContent = trafficData.dummy.filter(v => v !== null).length;
  document.getElementById("statEntropy").textContent = data.entropy.toFixed(3);
  document.getElementById("statDisc").textContent = (data.discriminability || 0).toFixed(3);
  document.getElementById("statPQ").textContent = data.pq_mode === "real (liboqs)" ? "Real PQ" : "Sim";

  // Log
  addLogEntry(data);
}

function updateStats(stats) {
  if (stats.total_packets !== undefined) {
    document.getElementById("statTotal").textContent = stats.total_packets;
  }
}

// ── Charts ─────────────────────────────────────────────────────────────────
const CHART_DEFAULTS = {
  responsive: true,
  animation: false,
  plugins: {
    legend: { labels: { color: "#94a3b8", font: { family: "Inter", size: 11 } } },
  },
  scales: {
    x: { display: false },
    y: { ticks: { color: "#64748b" }, grid: { color: "#1d2841" } },
  },
};

function initCharts() {
  const tCtx = document.getElementById("trafficChart").getContext("2d");
  trafficChart = new Chart(tCtx, {
    type: "line",
    data: {
      labels: trafficData.labels,
      datasets: [
        { label: "Real", data: trafficData.real, borderColor: "#06b6d4", backgroundColor: "#06b6d422", pointRadius: 4, pointHoverRadius: 6, spanGaps: true },
        { label: "Dummy", data: trafficData.dummy, borderColor: "#ef4444", backgroundColor: "#ef444422", pointRadius: 4, pointHoverRadius: 6, spanGaps: true },
      ],
    },
    options: { ...CHART_DEFAULTS, scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, title: { display: true, text: "Size (bytes)", color: "#64748b" } } } },
  });

  const eCtx = document.getElementById("entropyChart").getContext("2d");
  entropyChart = new Chart(eCtx, {
    type: "line",
    data: {
      labels: entropyData.labels,
      datasets: [
        { label: "Entropy (bits/byte)", data: entropyData.values, borderColor: "#f59e0b", backgroundColor: "#f59e0b22", pointRadius: 0, fill: true },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        x: { display: false },
        y: { min: 0, max: 8.5, ticks: { color: "#64748b" }, grid: { color: "#1d2841" } },
      },
    },
  });
}

function updateTrafficChart() {
  if (!trafficChart) return;
  trafficChart.data.labels = trafficData.labels;
  trafficChart.data.datasets[0].data = trafficData.real;
  trafficChart.data.datasets[1].data = trafficData.dummy;
  trafficChart.update("none");
}

function updateEntropyChart() {
  if (!entropyChart) return;
  entropyChart.data.labels = entropyData.labels;
  entropyChart.data.datasets[0].data = entropyData.values;
  entropyChart.update("none");
}

function updateMultipath() {
  const total = pathCounts.reduce((a, b) => a + b, 0) || 1;
  [0, 1, 2].forEach(i => {
    const pct = (pathCounts[i] / total * 100).toFixed(0);
    document.getElementById(`path${i}bar`).style.width = `${pct}%`;
    document.getElementById(`path${i}count`).textContent = pathCounts[i];
  });
}

function resetCharts() {
  trafficData = { real: [], dummy: [], labels: [] };
  entropyData = { values: [], labels: [] };
  pathCounts = [0, 0, 0];
  packetIndex = 0;
  if (trafficChart) trafficChart.destroy();
  if (entropyChart) entropyChart.destroy();
  trafficChart = null; entropyChart = null;
}

// ── Log ────────────────────────────────────────────────────────────────────
function addLogEntry(data) {
  const log = document.getElementById("packetLog");
  const empty = log.querySelector(".log-empty");
  if (empty) empty.remove();

  // Header row on first entry
  if (log.children.length === 0) {
    const hdr = document.createElement("div");
    hdr.className = "log-entry log-header";
    hdr.innerHTML = `<span>Pkt#</span><span>Type</span><span>Size</span><span>Entropy</span><span>IAT</span><span>Path</span>`;
    log.appendChild(hdr);
  }

  const row = document.createElement("div");
  row.className = `log-entry ${data.is_dummy ? "dummy" : "real"}`;
  row.innerHTML = `
    <span>${packetIndex}</span>
    <span class="${data.is_dummy ? "log-dummy" : "log-real"}">${data.is_dummy ? "DUMMY" : "REAL"}</span>
    <span>${data.size}B</span>
    <span>${data.entropy.toFixed(3)}</span>
    <span>${data.iat_ms.toFixed(1)}ms</span>
    <span>Path ${data.path_id}</span>
  `;
  log.insertBefore(row, log.children[1] || null);
  if (log.children.length > 25) log.removeChild(log.lastChild);
}

// ── Crypto Keys ────────────────────────────────────────────────────────────
async function loadKeys() {
  try {
    const keys = await apiFetch("/api/crypto/keys");
    renderKeyList(keys);
  } catch (e) { console.warn("Could not load keys:", e.message); }
}

function renderKeyList(keys) {
  const el = document.getElementById("keyList");
  if (!keys || keys.length === 0) {
    el.innerHTML = '<div class="empty-state" style="padding:8px">No keys yet</div>';
    return;
  }
  el.innerHTML = keys.map(k => `
    <div class="key-item">
      <span class="key-alg">${k.algorithm}</span>
      <span class="key-type">${k.key_type}</span>
    </div>
  `).join("");
}

async function generateKeys() {
  const alg = document.getElementById("keyAlgorithm").value;
  try {
    const keys = await apiFetch("/api/crypto/keys/generate", {
      method: "POST",
      body: JSON.stringify({ algorithm: alg }),
    });
    toast(`✅ ${alg} keypair generated (${keys.length} keys stored)`);
    await loadKeys();
  } catch (e) { toast(e.message, "error"); }
}

// ── Tabs ───────────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${target}`).classList.add("active");
      if (target === "traffic" && !trafficChart) initCharts();
    });
  });
}

// ── Modal helpers ──────────────────────────────────────────────────────────
function showModal(id) { document.getElementById(id).classList.remove("hidden"); }
function hideModal(id) { document.getElementById(id).classList.add("hidden"); }

// ── Event Listeners ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  updateUI();
  initCharts();

  // Auth buttons
  ["loginBtn", "heroLoginBtn"].forEach(id =>
    document.getElementById(id)?.addEventListener("click", () => showModal("loginModal"))
  );
  ["registerBtn", "heroRegisterBtn"].forEach(id =>
    document.getElementById(id)?.addEventListener("click", () => showModal("registerModal"))
  );
  document.getElementById("closeLoginModal").addEventListener("click", () => hideModal("loginModal"));
  document.getElementById("closeRegisterModal").addEventListener("click", () => hideModal("registerModal"));
  document.getElementById("switchToRegister").addEventListener("click", e => {
    e.preventDefault(); hideModal("loginModal"); showModal("registerModal");
  });
  document.getElementById("switchToLogin").addEventListener("click", e => {
    e.preventDefault(); hideModal("registerModal"); showModal("loginModal");
  });
  document.getElementById("logoutBtn").addEventListener("click", doLogout);

  // Login submit
  document.getElementById("submitLogin").addEventListener("click", async () => {
    clearError("loginError");
    const u = document.getElementById("loginUsername").value.trim();
    const p = document.getElementById("loginPassword").value;
    if (!u || !p) { showError("loginError", "Fill in all fields"); return; }
    try {
      await doLogin(u, p);
      hideModal("loginModal");
      updateUI();
      toast(`Welcome back, ${u}! 🛡️`);
    } catch (e) { showError("loginError", e.message); }
  });

  // Register submit
  document.getElementById("submitRegister").addEventListener("click", async () => {
    clearError("registerError");
    const u = document.getElementById("regUsername").value.trim();
    const e = document.getElementById("regEmail").value.trim();
    const p = document.getElementById("regPassword").value;
    if (!u || !e || !p) { showError("registerError", "Fill in all fields"); return; }
    try {
      await doRegister(u, e, p);
      await doLogin(u, p);
      hideModal("registerModal");
      updateUI();
      toast(`Account created! Welcome, ${u} 🎉`);
    } catch (err) { showError("registerError", err.message); }
  });

  // Dashboard controls
  document.getElementById("createSessionBtn").addEventListener("click", createSession);
  document.getElementById("startEngineBtn").addEventListener("click", startEngine);
  document.getElementById("stopEngineBtn").addEventListener("click", stopEngine);
  document.getElementById("sendDataBtn").addEventListener("click", sendData);
  document.getElementById("generateKeyBtn").addEventListener("click", generateKeys);

  // Close modals on overlay click
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", e => {
      if (e.target === overlay) overlay.classList.add("hidden");
    });
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay").forEach(m => m.classList.add("hidden"));
    }
  });
});
