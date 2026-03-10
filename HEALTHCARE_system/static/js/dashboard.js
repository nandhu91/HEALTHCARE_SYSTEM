/* dashboard.js — loads stats and today's appointment/emergency tables */

async function loadDashboard() {
  try {
    const summary = await apiFetch("/appointments/summary/today");
    const stats   = await apiFetch("/triage/stats");

    document.getElementById("d_total").textContent     = summary.total     ?? 0;
    document.getElementById("d_emergency").textContent = summary.emergency  ?? 0;
    document.getElementById("d_confirmed").textContent = summary.confirmed  ?? 0;
    document.getElementById("d_triage_total").textContent = stats.total    ?? 0;

    // Load today's appointments
    const appts = await apiFetch("/appointments/?page=1");
    renderDashboardTable(appts.appointments || []);

  } catch (e) {
    // If not logged in yet, ignore
  }
}

function renderDashboardTable(appointments) {
  const tbody = document.getElementById("dash_appt_table");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (appointments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:20px;">
      No appointments today.</td></tr>`;
    return;
  }

  appointments.slice(0, 8).forEach(a => {
    const dt  = new Date(a.appointment_dt).toLocaleString("en-IN", {
      day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit"
    });
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${a.patient_name || "—"}</td>
      <td>${a.department.replace(/_/g, " ")}</td>
      <td>${dt}</td>
      <td><span class="badge ${a.triage_level.toLowerCase()}">${a.triage_level}</span></td>
      <td><span class="badge ${a.status}">${a.status}</span></td>`;
    tbody.appendChild(row);
  });
}