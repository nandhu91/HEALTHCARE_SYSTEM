/* app.js — Shared state, navigation, API helper, toast */

const API  = "/api";
let   TOKEN = localStorage.getItem("mt_token") || "";

/* ── API helper ─────────────────────────────────────────────────────────── */
async function apiFetch(path, method = "GET", body = null) {
  const opts = {
    method,
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${TOKEN}`,
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(API + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

/* ── Toast ──────────────────────────────────────────────────────────────── */
function showToast(msg, isError = false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className   = "toast show" + (isError ? " error" : "");
  clearTimeout(t._tid);
  t._tid = setTimeout(() => (t.className = "toast"), 3200);
}

/* ── Navigation ─────────────────────────────────────────────────────────── */
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll("nav button[data-page]").forEach(b => b.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  const btn = document.querySelector(`nav button[data-page="${id}"]`);
  if (btn) btn.classList.add("active");

  // Load page data
  if      (id === "dashboard")     loadDashboard();
  else if (id === "appointments")  loadAppointments();
  else if (id === "triage_logs")   loadTriageLogs();
  else if (id === "notifications") loadNotifications();
}

/* ── Auth guard ─────────────────────────────────────────────────────────── */
function setToken(t) {
  TOKEN = t;
  localStorage.setItem("mt_token", t);
}
function logout() {
  TOKEN = "";
  localStorage.removeItem("mt_token");
  document.getElementById("app-shell").style.display  = "none";
  document.getElementById("login-page").style.display = "flex";
}

/* ── DOM ready ──────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  if (TOKEN) {
    showAppShell();
  } else {
    document.getElementById("login-page").style.display = "flex";
  }
});

function showAppShell() {
  document.getElementById("login-page").style.display = "none";
  document.getElementById("app-shell").style.display  = "block";
  showPage("dashboard");
}