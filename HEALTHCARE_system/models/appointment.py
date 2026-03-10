from datetime import datetime
from . import db


class Appointment(db.Model):
    __tablename__ = "appointments"

    STATUS_CHOICES = ["pending", "confirmed", "cancelled", "completed", "no_show"]
    DEPT_CHOICES   = [
        "general_medicine", "cardiology", "orthopedics",
        "neurology", "pediatrics", "emergency", "dermatology", "gynecology"
    ]

    id             = db.Column(db.Integer,     primary_key=True)
    patient_id     = db.Column(db.Integer,     db.ForeignKey("patients.id"), nullable=False)
    doctor_id      = db.Column(db.Integer,     db.ForeignKey("doctors.id"),  nullable=True)
    department     = db.Column(db.String(60),  nullable=False)
    appointment_dt = db.Column(db.DateTime,    nullable=False)
    symptoms       = db.Column(db.Text,        default="")
    triage_level   = db.Column(db.String(20),  default="NORMAL")
    triage_score   = db.Column(db.Integer,     default=0)
    status         = db.Column(db.String(20),  default="pending")
    notes          = db.Column(db.Text,        default="")
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":             self.id,
            "patient_id":     self.patient_id,
            "patient_name":   self.patient.name if self.patient else None,
            "doctor_id":      self.doctor_id,
            "doctor_name":    f"Dr. {self.doctor.name}" if self.doctor else None,
            "department":     self.department,
            "appointment_dt": self.appointment_dt.isoformat(),
            "symptoms":       self.symptoms,
            "triage_level":   self.triage_level,
            "triage_score":   self.triage_score,
            "status":         self.status,
            "notes":          self.notes,
            "created_at":     self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Appointment {self.id} | Patient {self.patient_id} | {self.status}>"