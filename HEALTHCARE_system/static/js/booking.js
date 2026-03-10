/* booking.js — appointment booking form logic */

async function bookAppointment() {
  const name    = document.getElementById("b_name").value.trim();
  const age     = document.getElementById("b_age").value;
  const phone   = document.getElementById("b_phone").value.trim();
  const dept    = document.getElementById("b_dept").value;
  const date    = document.getElementById("b_date").value;
  const time    = document.getElementById("b_time").value;
  const symptoms= document.getElementById("b_symptoms").value.trim();
  const temp    = parseFloat(document.getElementById("b_temp").value)  || 98.6;
  const o2      = parseFloat(document.getElementById("b_o2").value)    || 98.0;
  const ageGrp  = document.getElementById("b_age_group").value;

  if (!name || !age || !phone || !dept || !date || !time) {
    showToast("Please fill all required fields.", true);
    return;
  }

  const appt_dt = `${date}T${time}`;

  try {
    // 1. Create/find patient
    let patient;
    try {
      const res = await apiFetch("/patients/", "POST", {
        name, age: parseInt(age), phone,
        email: document.getElementById("b_email").value.trim() || undefined,
      });
      patient = res;
    } catch (e) {
      // Patient might already exist — search by phone
      const list = await apiFetch(`/patients/?q=${encodeURIComponent(phone)}`);
      patient = list.patients?.[0];
      if (!patient) throw new Error("Could not create or find patient.");
    }

    // 2. Book appointment
    const data = await apiFetch("/appointments/", "POST", {
      patient_id:    patient.id,
      department:    dept,
      appointment_dt:appt_dt,
      symptoms,
      temperature:   temp,
      o2_saturation: o2,
      age_group:     ageGrp,
    });

    showTriageResult(data.triage, data.appointment);
    showToast(`Appointment #A${String(data.appointment.id).padStart(4,"0")} booked!`);
    clearBookingForm();
    loadAppointments();

  } catch (err) {
    showToast(err.message, true);
  }
}

function showTriageResult(triage, appointment) {
  const box   = document.getElementById("book_triage");
  const level = document.getElementById("bt_level");
  const advice= document.getElementById("bt_advice");

  box.classList.add("show");
  if (triage.level === "EMERGENCY") {
    box.className   = "triage-result show emergency";
    level.style.color = "var(--danger)";
    level.textContent = "🚨 EMERGENCY — Priority Queue";
    advice.textContent = "Critical indicators found. Patient added to emergency queue. Medical staff has been alerted.";
  } else {
    box.className   = "triage-result show normal";
    level.style.color = "var(--accent)";
    level.textContent = "✅ NORMAL — Standard Queue";
    advice.textContent = "No critical indicators. Appointment confirmed. SMS and email reminder will be sent.";
  }
}

function clearBookingForm() {
  ["b_name","b_age","b_phone","b_email","b_date","b_symptoms","b_temp","b_o2"]
    .forEach(id => { const el = document.getElementById(id); if(el) el.value = ""; });
  ["b_dept","b_time","b_age_group"].forEach(id => {
    const el = document.getElementById(id); if(el) el.selectedIndex = 0;
  });
  const box = document.getElementById("book_triage");
  if (box) box.className = "triage-result";
}

async function loadAppointments() {
  try {
    const data  = await apiFetch("/appointments/");
    const tbody = document.getElementById("appt_table_body");
    if (!tbody) return;
    tbody.innerHTML = "";

    (data.appointments || []).forEach(a => {
      const dt  = new Date(a.appointment_dt).toLocaleString("en-IN", {
        day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit"
      });
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>#A${String(a.id).padStart(4,"0")}</td>
        <td>${a.patient_name || "—"}</td>
        <td>${a.department.replace(/_/g," ")}</td>
        <td>${dt}</td>
        <td><span class="badge ${a.triage_level.toLowerCase()}">${a.triage_level}</span></td>
        <td><span class="badge ${a.status}">${a.status}</span></td>
        <td>
          <button class="btn btn-sm btn-outline"
            onclick="cancelAppt(${a.id})">Cancel</button>
        </td>`;
      tbody.appendChild(row);
    });
  } catch (e) { /* silently fail if not loaded yet */ }
}

async function cancelAppt(id) {
  if (!confirm("Cancel this appointment?")) return;
  try {
    await apiFetch(`/appointments/${id}`, "DELETE");
    showToast("Appointment cancelled.");
    loadAppointments();
  } catch (e) {
    showToast(e.message, true);
  }
}