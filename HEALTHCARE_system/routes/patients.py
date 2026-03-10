from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db
from models.patient import Patient

patients_bp = Blueprint("patients", __name__)


@patients_bp.get("/")
@jwt_required()
def list_patients():
    page   = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")

    query = Patient.query
    if search:
        query = query.filter(
            Patient.name.ilike(f"%{search}%") |
            Patient.phone.ilike(f"%{search}%")
        )

    paginator = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return jsonify({
        "patients":     [p.to_dict() for p in paginator.items],
        "total":        paginator.total,
        "pages":        paginator.pages,
        "current_page": paginator.page,
    }), 200


@patients_bp.post("/")
@jwt_required()
def create_patient():
    data = request.get_json() or {}
    for field in ("name", "age", "phone"):
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    if Patient.query.filter_by(phone=data["phone"]).first():
        return jsonify({"error": "Phone number already registered"}), 409

    patient = Patient(
        name            = data["name"],
        age             = int(data["age"]),
        gender          = data.get("gender"),
        phone           = data["phone"],
        email           = data.get("email"),
        blood_group     = data.get("blood_group"),
        medical_history = data.get("medical_history", ""),
        address         = data.get("address", ""),
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify(patient.to_dict()), 201


@patients_bp.get("/<int:patient_id>")
@jwt_required()
def get_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict()), 200


@patients_bp.put("/<int:patient_id>")
@jwt_required()
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    data    = request.get_json() or {}

    for field in ("name", "age", "gender", "email", "blood_group", "medical_history", "address"):
        if field in data:
            setattr(patient, field, data[field])

    db.session.commit()
    return jsonify(patient.to_dict()), 200


@patients_bp.delete("/<int:patient_id>")
@jwt_required()
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": f"Patient {patient_id} deleted"}), 200


@patients_bp.get("/<int:patient_id>/appointments")
@jwt_required()
def patient_appointments(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify([a.to_dict() for a in patient.appointments]), 200


@patients_bp.get("/<int:patient_id>/triage-history")
@jwt_required()
def patient_triage_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify([t.to_dict() for t in patient.triage_logs]), 200