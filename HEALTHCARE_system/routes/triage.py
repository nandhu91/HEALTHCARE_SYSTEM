from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db
from models.patient import Patient
from models.triage_log import TriageLog
from models.notification import Notification
from services.triage_engine import classify_patient, classify_from_text
from services.notification_service import notify_emergency_alert

triage_bp = Blueprint("triage", __name__)


@triage_bp.post("/classify")
@jwt_required()
def classify():
    """
    POST /api/triage/classify
    {
        "patient_id":    1,
        "symptoms":      ["chest_pain", "high_fever"],
        "symptoms_text": "patient complains of chest pain",   <- alternative to symptoms list
        "temperature":   103.5,
        "o2_saturation": 91.0,
        "age_group":     "senior"
    }
    """
    data = request.get_json() or {}
    if not data.get("patient_id"):
        return jsonify({"error": "patient_id is required"}), 400

    patient = Patient.query.get(data["patient_id"])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    temperature   = float(data.get("temperature",   98.6))
    o2_saturation = float(data.get("o2_saturation", 98.0))
    age_group     = data.get("age_group", "adult")

    if data.get("symptoms"):
        result       = classify_patient(data["symptoms"], temperature, o2_saturation, age_group)
        symptoms_str = ",".join(data["symptoms"])
    elif data.get("symptoms_text"):
        result       = classify_from_text(data["symptoms_text"], temperature, o2_saturation, age_group)
        symptoms_str = data["symptoms_text"]
    else:
        return jsonify({"error": "Provide 'symptoms' list or 'symptoms_text' string"}), 400

    # Save log
    log = TriageLog(
        patient_id    = patient.id,
        symptoms      = symptoms_str,
        temperature   = temperature,
        o2_saturation = o2_saturation,
        age_group     = age_group,
        triage_result = result.level,
        triage_score  = result.score,
        reasoning     = " | ".join(result.reasoning),
    )
    db.session.add(log)

    if result.level == "EMERGENCY":
        alert = Notification(
            patient_id = patient.id,
            notif_type = "emergency_alert",
            channel    = "all",
            title      = f"🚨 Emergency Alert — {patient.name}",
            message    = (
                f"EMERGENCY triage. Temp: {temperature}°F | "
                f"O2: {o2_saturation}% | Symptoms: {symptoms_str}"
            ),
            status    = "pending",
            is_urgent = True,
        )
        db.session.add(alert)
        db.session.commit()
        try:
            notify_emergency_alert(patient, log)
            alert.status  = "sent"
            alert.sent_at = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.commit()
    else:
        db.session.commit()

    return jsonify({
        "triage_log_id": log.id,
        "patient":       patient.to_dict(),
        "result":        result.to_dict(),
    }), 200


@triage_bp.get("/logs")
@jwt_required()
def triage_logs():
    page  = request.args.get("page", 1, type=int)
    level = request.args.get("level")
    query = TriageLog.query
    if level:
        query = query.filter_by(triage_result=level.upper())
    paginator = query.order_by(TriageLog.classified_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return jsonify({
        "logs":  [l.to_dict() for l in paginator.items],
        "total": paginator.total,
    }), 200


@triage_bp.get("/logs/<int:log_id>")
@jwt_required()
def get_log(log_id):
    return jsonify(TriageLog.query.get_or_404(log_id).to_dict()), 200


@triage_bp.get("/stats")
@jwt_required()
def stats():
    total     = TriageLog.query.count()
    emergency = TriageLog.query.filter_by(triage_result="EMERGENCY").count()
    normal    = TriageLog.query.filter_by(triage_result="NORMAL").count()
    return jsonify({
        "total":         total,
        "emergency":     emergency,
        "normal":        normal,
        "emergency_pct": round(emergency / total * 100, 1) if total else 0,
    }), 200