/* notifications.js — load and display notifications */

async function loadNotifications() {
  try {
    const data = await apiFetch("/notifications/");
    const list = document.getElementById("notif_list");
    if (!list) return;
    list.innerHTML = "";

    if (!data.notifications?.length) {
      list.innerHTML = `<div style="color:var(--muted);text-align:center;padding:30px;">
        No notifications yet.</div>`;
      return;
    }

    data.notifications.forEach(n => {
      const ago  = timeAgo(n.created_at);
      const icon = n.notif_type === "emergency_alert" ? "🚨"
                 : n.notif_type === "confirmation"    ? "✅"
                 : n.notif_type === "reminder"        ? "📅"
                 : "📊";
      const div  = document.createElement("div");
      div.className = `notif-item ${n.status !== "read" ? "unread" : ""} ${n.is_urgent ? "urgent" : ""}`;
      div.innerHTML = `
        <div class="notif-icon">${icon}</div>
        <div class="notif-content">
          <div class="notif-title">${n.title}</div>
          <div class="notif-msg">${n.message}</div>
        </div>
        <div class="notif-time">${ago}</div>`;
      if (n.status !== "read") {
        div.addEventListener("click", () => markRead(n.id, div));
      }
      list.appendChild(div);
    });
  } catch (e) { /* ignore */ }
}

async function markRead(id, el) {
  try {
    await apiFetch(`/notifications/${id}/read`, "PATCH");
    el.classList.remove("unread", "urgent");
  } catch (e) { /* ignore */ }
}

async function sendTestNotification(type) {
  const patientId = prompt("Enter Patient ID:");
  if (!patientId) return;
  try {
    if (type === "emergency") {
      await apiFetch("/notifications/send", "POST", {
        patient_id: parseInt(patientId),
        title:      "🚨 Emergency Alert Test",
        message:    "This is a test emergency alert from MediTriage.",
        notif_type: "emergency_alert",
        is_urgent:  true,
      });
    } else {
      await apiFetch("/notifications/send", "POST", {
        patient_id: parseInt(patientId),
        title:      "📅 Appointment Reminder",
        message:    "Your appointment is scheduled for tomorrow. Please arrive 10 minutes early.",
        notif_type: "reminder",
      });
    }
    showToast("Notification sent!");
    loadNotifications();
  } catch (e) {
    showToast(e.message, true);
  }
}

function timeAgo(isoStr) {
  const diff = (Date.now() - new Date(isoStr)) / 1000;
  if (diff < 60)     return "Just now";
  if (diff < 3600)   return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400)  return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}