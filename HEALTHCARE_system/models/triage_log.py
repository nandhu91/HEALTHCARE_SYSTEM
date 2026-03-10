from datetime import datetime
from . import db


class TriageLog(db.Model):
    __tablename__ = "triage_logs"

    id            = db.Column(db.Integer,    primary_key=True)
    patient_id    = db.Column(db.Integer,    db.ForeignKey("patients.id"), nullable=False)
    symptoms      = db.Column(db.Text,       default="")        # comma-separated keys
    temperature   = db.Column(db.Float,      default=98.6)      # Fahrenheit
    o2_saturation = db.Column(db.Float,      default=98.0)      # percentage
    age_group     = db.Column(db.String(10), default="adult")   # adult|child|senior
    triage_result = db.Column(db.String(20), nullable=False)    # NORMAL|EMERGENCY
    triage_score  = db.Column(db.Integer,    default=0)
    reasoning     = db.Column(db.Text,       default="")
    classified_at = db.Column(db.DateTime,   default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":            self.id,
            "patient_id":    self.patient_id,
            "patient_name":  self.patient.name if self.patient else None,
            "symptoms":      self.symptoms.split(",") if self.symptoms else [],
            "temperature":   self.temperature,
            "o2_saturation": self.o2_saturation,
            "age_group":     self.age_group,
            "triage_result": self.triage_result,
            "triage_score":  self.triage_score,
            "reasoning":     self.reasoning,
            "classified_at": self.classified_at.isoformat(),
        }

    def __repr__(self):
        return f"<TriageLog {self.id}: {self.triage_result}>"