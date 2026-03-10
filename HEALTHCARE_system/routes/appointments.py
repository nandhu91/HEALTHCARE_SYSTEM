from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db
from models.appointment import Appointment
from models.patient import Patient
from models.notification import Notification
from services.triage_engine import classify_from_text, classify_patient
from services.notification_service import notify_appointment_confirmation

appointments_bp = Blueprint("appointments", __name__)


def _parse_dt(s):
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}")


@appointments_bp.get("/")
@jwt_required()
def list_appointments():
    page     = request.args.get("page", 1, type=int)
    status   = request.args.get("status")
    dept     = request.args.get("department")
    triage   = request.args.get("triage_level")
    date_str = request.args.get("date")

    query = Appointment.query
    if status: query = query.filter_by(status=status)
    if dept:   query = query.filter_by(department=dept)
    if triage: query = query.filter_by(triage_level=triage.upper())
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            query = query.filter(db.func.date(Appointment.appointment_dt) == d.date())
        except ValueError:
            pass

    paginator = query.order_by(Appointment.appointment_dt.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return jsonify({
        "appointments": [a.to_dict() for a in paginator.items],
        "total":        paginator.total,
        "pages":        paginator.pages,
    }), 200


@appointments_bp.post("/")
@jwt_required()
def book_appointment():
    data = request.get_json() or {}
    for field in ("patient_id", "department", "appointment_dt"):
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    patient = Patient.query.get(data["patient_id"])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    try:
        appt_dt = _parse_dt(data["appointment_dt"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if appt_dt < datetime.utcnow():
        return jsonify({"error": "Appointment date cannot be in the past"}), 400

    symptoms_text = data.get("symptoms", "")
    age_group     = data.get("age_group", "adult")

    # Run triage
    if data.get("symptom_keys"):
        triage_result = classify_patient(
            symptoms      = data["symptom_keys"],
            temperature   = float(data.get("temperature",   98.6)),
            o2_saturation = float(data.get("o2_saturation", 98.0)),
            age_group     = age_group,
        )
    else:
        triage_result = classify_from_text(
            text          = symptoms_text,
            temperature   = float(data.get("temperature",   98.6)),
            o2_saturation = float(data.get("o2_saturation", 98.0)),
            age_group     = age_group,
        )

    appt = Appointment(
        patient_id     = patient.id,
        doctor_id      = data.get("doctor_id"),
        department     = data["department"],
        appointment_dt = appt_dt,
        symptoms       = symptoms_text,
        triage_level   = triage_result.level,
        triage_score   = triage_result.score,
        status         = "confirmed",
        notes          = data.get("notes", ""),
    )
    db.session.add(appt)
    db.session.flush()   # get appt.id before commit

    notif = Notification(
        patient_id = patient.id,
        notif_type = "confirmation",
        channel    = "all",
        title      = f"Appointment Confirmed — #A{appt.id:04d}",
        message    = (
            f"Your appointment on "
            f"{appt_dt.strftime('%d %b %Y at %I:%M %p')} is confirmed."
        ),
        status    = "pending",
        is_urgent = (triage_result.level == "EMERGENCY"),
    )
    db.session.add(notif)
    db.session.commit()

    # Try to send SMS/email (won't crash if it fails)
    try:
        notify_appointment_confirmation(patient, appt)
        notif.status  = "sent"
        notif.sent_at = datetime.utcnow()
        db.session.commit()
    except Exception:
        pass

    return jsonify({
        "appointment": appt.to_dict(),
        "triage":      triage_result.to_dict(),
        "message":     "Appointment booked successfully",
    }), 201


@appointments_bp.get("/<int:appt_id>")
@jwt_required()
def get_appointment(appt_id):
    return jsonify(Appointment.query.get_or_404(appt_id).to_dict()), 200


@appointments_bp.patch("/<int:appt_id>/status")
@jwt_required()
def update_status(appt_id):
    appt   = Appointment.query.get_or_404(appt_id)
    status = (request.get_json() or {}).get("status")
    if status not in Appointment.STATUS_CHOICES:
        return jsonify({"error": f"Valid statuses: {Appointment.STATUS_CHOICES}"}), 400
    appt.status = status
    db.session.commit()
    return jsonify(appt.to_dict()), 200


@appointments_bp.patch("/<int:appt_id>/reschedule")
@jwt_required()
def reschedule(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    try:
        new_dt = _parse_dt((request.get_json() or {})["appointment_dt"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    appt.appointment_dt = new_dt
    appt.status         = "confirmed"
    db.session.commit()
    return jsonify(appt.to_dict()), 200


@appointments_bp.delete("/<int:appt_id>")
@jwt_required()
def cancel_appointment(appt_id):
    appt        = Appointment.query.get_or_404(appt_id)
    appt.status = "cancelled"
    db.session.commit()
    return jsonify({"message": f"Appointment {appt_id} cancelled"}), 200


@appointments_bp.get("/summary/today")
@jwt_required()
def today_summary():
    today     = datetime.utcnow().date()
    all_today = Appointment.query.filter(
        db.func.date(Appointment.appointment_dt) == today
    ).all()
    return jsonify({
        "total":     len(all_today),
        "confirmed": sum(1 for a in all_today if a.status    == "confirmed"),
        "completed": sum(1 for a in all_today if a.status    == "completed"),
        "cancelled": sum(1 for a in all_today if a.status    == "cancelled"),
        "emergency": sum(1 for a in all_today if a.triage_level == "EMERGENCY"),
        "normal":    sum(1 for a in all_today if a.triage_level == "NORMAL"),
    }), 200