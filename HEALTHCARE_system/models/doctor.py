from datetime import datetime
from . import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id             = db.Column(db.Integer,     primary_key=True)
    name           = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(80),  nullable=False)
    department     = db.Column(db.String(60),  nullable=False)
    phone          = db.Column(db.String(20),  nullable=True)
    email          = db.Column(db.String(120), nullable=True)
    available      = db.Column(db.Boolean,     default=True)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True)

    def to_dict(self):
        return {
            "id":             self.id,
            "name":           self.name,
            "specialization": self.specialization,
            "department":     self.department,
            "phone":          self.phone,
            "email":          self.email,
            "available":      self.available,
        }

    def __repr__(self):
        return f"<Doctor {self.id}: Dr. {self.name}>"