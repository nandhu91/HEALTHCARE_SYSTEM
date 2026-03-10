"""
services/notification_service.py
=================================
Handles SMS via Twilio and Email via SMTP.
In development/testing the messages are logged instead of sent.
"""

import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level senders
# ---------------------------------------------------------------------------

def send_email(to_address: str, subject: str, body_html: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    if not to_address:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = current_app.config["MAIL_SENDER"]
        msg["To"]      = to_address
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(current_app.config["MAIL_SERVER"],
                          current_app.config["MAIL_PORT"]) as server:
            server.ehlo()
            if current_app.config.get("MAIL_USE_TLS"):
                server.starttls()
            server.login(current_app.config["MAIL_USERNAME"],
                         current_app.config["MAIL_PASSWORD"])
            server.sendmail(msg["From"], [to_address], msg.as_string())

        logger.info("Email sent → %s | %s", to_address, subject)
        return True

    except Exception as exc:
        logger.warning("Email FAILED → %s : %s", to_address, exc)
        # In dev, just log – don't crash the app
        return False


def send_sms(to_number: str, message: str) -> bool:
    """Send SMS via Twilio. Returns True on success."""
    if not to_number:
        return False
    try:
        from twilio.rest import Client
        client = Client(current_app.config["TWILIO_ACCOUNT_SID"],
                        current_app.config["TWILIO_AUTH_TOKEN"])
        msg = client.messages.create(
            body  = message,
            from_ = current_app.config["TWILIO_FROM_NUMBER"],
            to    = to_number,
        )
        logger.info("SMS sent → %s | SID: %s", to_number, msg.sid)
        return True

    except Exception as exc:
        logger.warning("SMS FAILED → %s : %s", to_number, exc)
        return False


# ---------------------------------------------------------------------------
# High-level notification helpers
# ---------------------------------------------------------------------------

def notify_appointment_confirmation(patient, appointment) -> dict:
    """Confirmation SMS + email after booking."""
    dt_str   = appointment.appointment_dt.strftime("%A, %d %B %Y at %I:%M %p")
    dept_str = appointment.department.replace("_", " ").title()

    sms = (
        f"Hi {patient.name}, your MediTriage appointment is CONFIRMED.\n"
        f"Dept: {dept_str} | {dt_str}\n"
        f"Booking ID: #A{appointment.id:04d}\n"
        "Please arrive 10 mins early."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                padding:24px;background:#f9fafb;border-radius:12px;">
      <h2 style="color:#00d4aa">✅ Appointment Confirmed</h2>
      <p>Dear <strong>{patient.name}</strong>,</p>
      <p>Your appointment has been confirmed:</p>
      <table style="width:100%;border-collapse:collapse;margin-top:16px;">
        <tr><td style="padding:8px;color:#555;">Department</td>
            <td style="padding:8px;font-weight:bold;">{dept_str}</td></tr>
        <tr style="background:#f0faf7;">
            <td style="padding:8px;color:#555;">Date &amp; Time</td>
            <td style="padding:8px;font-weight:bold;">{dt_str}</td></tr>
        <tr><td style="padding:8px;color:#555;">Booking ID</td>
            <td style="padding:8px;font-weight:bold;">#A{appointment.id:04d}</td></tr>
        <tr style="background:#f0faf7;">
            <td style="padding:8px;color:#555;">Triage Level</td>
            <td style="padding:8px;font-weight:bold;">{appointment.triage_level}</td></tr>
      </table>
      <p style="margin-top:20px;color:#555;">Please bring a valid ID and arrive 10 minutes early.</p>
      <p style="color:#aaa;font-size:12px;">MediTriage — Smart Healthcare System</p>
    </div>"""

    return {
        "sms_ok":   send_sms(patient.phone, sms),
        "email_ok": send_email(patient.email,
                               "Appointment Confirmed — MediTriage", html),
    }


def notify_emergency_alert(patient, triage_log) -> dict:
    """Emergency alert SMS + email to patient/staff."""
    sms = (
        f"EMERGENCY ALERT — {patient.name}\n"
        f"O2: {triage_log.o2_saturation}%  Temp: {triage_log.temperature}°F\n"
        f"Symptoms: {triage_log.symptoms}\n"
        "Immediate medical attention required!"
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                padding:24px;background:#fff0f3;border:2px solid #ff4d6d;border-radius:12px;">
      <h2 style="color:#ff4d6d">🚨 EMERGENCY TRIAGE ALERT</h2>
      <p><strong>Patient:</strong> {patient.name} (Age group: {triage_log.age_group})</p>
      <p><strong>Temperature:</strong> {triage_log.temperature}°F</p>
      <p><strong>O2 Saturation:</strong> {triage_log.o2_saturation}%</p>
      <p><strong>Symptoms:</strong> {triage_log.symptoms}</p>
      <p><strong>Triage Score:</strong> {triage_log.triage_score}</p>
      <p style="color:#ff4d6d;font-weight:bold;">ACTION: Immediate physician attendance required.</p>
    </div>"""

    return {
        "sms_ok":   send_sms(patient.phone, sms),
        "email_ok": send_email(patient.email,
                               "🚨 EMERGENCY ALERT — MediTriage", html),
    }


def notify_appointment_reminder(patient, appointment) -> dict:
    """24-hour reminder SMS + email."""
    dt_str = appointment.appointment_dt.strftime("%A, %d %B at %I:%M %p")
    sms = (
        f"Reminder: {patient.name}, your MediTriage appointment is TOMORROW.\n"
        f"{dt_str} | #A{appointment.id:04d}\n"
        "Reply CANCEL to cancel."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                padding:24px;background:#fff8e6;border-radius:12px;">
      <h2 style="color:#ffb703">📅 Appointment Reminder</h2>
      <p>Dear <strong>{patient.name}</strong>,</p>
      <p>Your appointment is <strong>tomorrow</strong>:</p>
      <p style="font-size:1.15em;font-weight:bold;">{dt_str}</p>
      <p>Booking ID: <strong>#A{appointment.id:04d}</strong></p>
      <p style="color:#555;">Contact us to reschedule if needed.</p>
    </div>"""

    return {
        "sms_ok":   send_sms(patient.phone, sms),
        "email_ok": send_email(patient.email,
                               "Appointment Reminder — MediTriage", html),
    }