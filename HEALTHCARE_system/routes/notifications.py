from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db
from models.notification import Notification
from models.patient import Patient
from services.notification_service import (
    notify_appointment_reminder,
    send_sms,
    send_email,
)

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/")
@jwt_required()
def list_notifications():
    page       = request.args.get("page", 1, type=int)
    status     = request.args.get("status")
    patient_id = request.args.get("patient_id", type=int)
    urgent_str = request.args.get("urgent")

    query = Notification.query
    if status:     query = query.filter_by(status=status)
    if patient_id: query = query.filter_by(patient_id=patient_id)
    if urgent_str is not None:
        query = query.filter_by(is_urgent=(urgent_str.lower() == "true"))

    paginator = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return jsonify({
        "notifications": [n.to_dict() for n in paginator.items],
        "total":         paginator.total,
    }), 200


@notifications_bp.post("/send")
@jwt_required()
def send_custom():
    data = request.get_json() or {}
    for field in ("patient_id", "title", "message"):
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    patient = Patient.query.get(data["patient_id"])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    channel   = data.get("channel", "all")
    is_urgent = bool(data.get("is_urgent", False))
    sms_ok    = False
    email_ok  = False

    if channel in ("sms", "all"):
        sms_ok = send_sms(patient.phone, data["message"])
    if channel in ("email", "all"):
        email_ok = send_email(patient.email, data["title"], f"<p>{data['message']}</p>")

    notif = Notification(
        patient_id = patient.id,
        notif_type = data.get("notif_type", "system"),
        channel    = channel,
        title      = data["title"],
        message    = data["message"],
        status     = "sent" if (sms_ok or email_ok) else "failed",
        is_urgent  = is_urgent,
        sent_at    = datetime.utcnow(),
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "notification": notif.to_dict(),
        "delivery":     {"sms": sms_ok, "email": email_ok},
    }), 201


@notifications_bp.post("/remind/<int:appt_id>")
@jwt_required()
def send_reminder(appt_id):
    from models.appointment import Appointment
    appt   = Appointment.query.get_or_404(appt_id)
    result = notify_appointment_reminder(appt.patient, appt)
    return jsonify({"message": "Reminder sent", "delivery": result}), 200


@notifications_bp.patch("/<int:notif_id>/read")
@jwt_required()
def mark_read(notif_id):
    notif         = Notification.query.get_or_404(notif_id)
    notif.status  = "read"
    notif.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify(notif.to_dict()), 200


@notifications_bp.get("/unread-count")
@jwt_required()
def unread_count():
    total  = Notification.query.filter(Notification.status.in_(["pending", "sent"])).count()
    urgent = Notification.query.filter_by(is_urgent=True, status="sent").count()
    return jsonify({"unread": total, "urgent": urgent}), 200