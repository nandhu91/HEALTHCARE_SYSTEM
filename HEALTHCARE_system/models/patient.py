from datetime import datetime
from . import db


class Patient(db.Model):
    __tablename__ = "patients"

    id              = db.Column(db.Integer,     primary_key=True)
    name            = db.Column(db.String(120), nullable=False)
    age             = db.Column(db.Integer,     nullable=False)
    gender          = db.Column(db.String(10),  nullable=True)
    phone           = db.Column(db.String(20),  nullable=False, unique=True)
    email           = db.Column(db.String(120), nullable=True)
    blood_group     = db.Column(db.String(5),   nullable=True)
    medical_history = db.Column(db.Text,        default="")
    address         = db.Column(db.Text,        default="")
    created_at      = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments  = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")
    triage_logs   = db.relationship("TriageLog",   backref="patient", lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship("Notification",backref="patient", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":              self.id,
            "name":            self.name,
            "age":             self.age,
            "gender":          self.gender,
            "phone":           self.phone,
            "email":           self.email,
            "blood_group":     self.blood_group,
            "medical_history": self.medical_history,
            "address":         self.address,
            "created_at":      self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Patient {self.id}: {self.name}>"