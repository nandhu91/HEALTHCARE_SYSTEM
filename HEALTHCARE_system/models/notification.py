from datetime import datetime
from . import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.Integer,     primary_key=True)
    patient_id = db.Column(db.Integer,     db.ForeignKey("patients.id"), nullable=False)
    notif_type = db.Column(db.String(30),  nullable=False)   # reminder|confirmation|emergency_alert|system
    channel    = db.Column(db.String(20),  default="all")    # sms|email|all
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text,        nullable=False)
    status     = db.Column(db.String(20),  default="pending") # pending|sent|failed|read
    is_urgent  = db.Column(db.Boolean,     default=False)
    sent_at    = db.Column(db.DateTime,    nullable=True)
    read_at    = db.Column(db.DateTime,    nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "patient_id":  self.patient_id,
            "patient_name":self.patient.name if self.patient else None,
            "notif_type":  self.notif_type,
            "channel":     self.channel,
            "title":       self.title,
            "message":     self.message,
            "status":      self.status,
            "is_urgent":   self.is_urgent,
            "sent_at":     self.sent_at.isoformat()    if self.sent_at    else None,
            "read_at":     self.read_at.isoformat()    if self.read_at    else None,
            "created_at":  self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Notification {self.id} | {self.notif_type} | {self.status}>"