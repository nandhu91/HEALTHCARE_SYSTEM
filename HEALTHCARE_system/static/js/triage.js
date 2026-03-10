/* triage.js — symptom checker + triage log */

const SYMPTOMS = [
  { id:"chest_pain",           label:"Chest Pain",            redFlag:true  },
  { id:"difficulty_breathing", label:"Difficulty Breathing",  redFlag:true  },
  { id:"unconscious",          label:"Unconscious",           redFlag:true  },
  { id:"severe_bleeding",      label:"Severe Bleeding",       redFlag:true  },
  { id:"stroke_signs",         label:"Stroke Signs",          redFlag:true  },
  { id:"seizure",              label:"Seizure",               redFlag:true  },
  { id:"cardiac_arrest",       label:"Cardiac Arrest",        redFlag:true  },
  { id:"anaphylaxis",          label:"Allergic Reaction",     redFlag:true  },
  { id:"high_fever",           label:"High Fever",            redFlag:false },
  { id:"severe_pain",          label:"Severe Pain",           redFlag:false },
  { id:"vomiting_blood",       label:"Vomiting Blood",        redFlag:false },
  { id:"confusion",            label:"Confusion",             redFlag:false },
  { id:"fracture",             label:"Fracture/Injury",       redFlag:false },
  { id:"dizziness",            label:"Dizziness",             redFlag:false },
  { id:"vomiting",             label:"Vomiting",              redFlag:false },
  { id:"headache",             label:"Headache",              redFlag:false },
  { id:"mild_cough",           label:"Mild Cough",            redFlag:false },
  { id:"fatigue",              label:"Fatigue",               redFlag:false },
];

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("symptom_checkboxes");
  if (!container) return;
  container.innerHTML = "";
  SYMPTOMS.forEach(s => {
    const lbl = document.createElement("label");
    lbl.className = "sym-label" + (s.redFlag ? " red-flag" : "");
    lbl.dataset.id = s.id;
    lbl.innerHTML  = `<input type="checkbox" value="${s.id}"> ${s.label}`;
    lbl.querySelector("input").addEventListener("change", function() {
      lbl.classList.toggle("checked", this.checked);
    });
    container.appendChild(lbl);
  });
});

async function runTriage() {
  const patientId = parseInt(document.getElementById("t_patient_id").value);
  const temp      = parseFloat(document.getElementById("t_temp").value) || 98.6;
  const o2        = parseFloat(document.getElementById("t_o2").value)   || 98.0;
  const ageGroup  = document.getElementById("t_age_group").value;
  const checked   = [...document.querySelectorAll("#symptom_checkboxes input:checked")]
                      .map(i => i.value);

  if (!patientId) {
    showToast("Enter a valid Patient ID.", true);
    return;
  }

  try {
    const data = await apiFetch("/triage/classify", "POST", {
      patient_id:    patientId,
      symptoms:      checked,
      temperature:   temp,
      o2_saturation: o2,
      age_group:     ageGroup,
    });

    renderTriageResult(data.result, data.patient);
    loadTriageLogs();
  } catch (err) {
    showToast(err.message, true);
  }
}

function renderTriageResult(result, patient) {
  const box   = document.getElementById("triage_result_box");
  const level = document.getElementById("tr_level");
  const advice= document.getElementById("tr_advice");
  const reason= document.getElementById("tr_reasoning");

  box.classList.add("show");
  if (result.level === "EMERGENCY") {
    box.className   = "triage-result show emergency";
    level.style.color = "var(--danger)";
    level.textContent = `🚨 EMERGENCY — ${patient?.name || "Patient"}`;
    advice.textContent= "Critical indicators detected. Immediate physician attention required.";
  } else {
    box.className   = "triage-result show normal";
    level.style.color = "var(--accent)";
    level.textContent = `✅ NORMAL — ${patient?.name || "Patient"}`;
    advice.textContent= `Score: ${result.score}. Patient placed in standard queue.`;
  }

  if (reason) {
    reason.innerHTML = result.reasoning.map(r => `<div style="margin-bottom:4px">• ${r}</div>`).join("");
  }
  showToast(`Triage complete: ${result.level}`, result.level === "EMERGENCY");
}

async function loadTriageLogs() {
  try {
    const data  = await apiFetch("/triage/logs");
    const tbody = document.getElementById("triage_log_table");
    if (!tbody) return;
    tbody.innerHTML = "";

    (data.logs || []).forEach(l => {
      const dt  = new Date(l.classified_at).toLocaleString("en-IN", {
        day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit"
      });
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${l.patient_name || "—"}</td>
        <td>${(l.symptoms || []).join(", ") || "—"}</td>
        <td>${l.temperature}°F</td>
        <td>${l.o2_saturation}%</td>
        <td>${dt}</td>
        <td><span class="badge ${l.triage_result.toLowerCase()}">${l.triage_result}</span></td>`;
      tbody.appendChild(row);
    });
  } catch (e) { /* ignore */ }
}