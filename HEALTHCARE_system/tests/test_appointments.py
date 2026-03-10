"""
tests/test_appointments.py
===========================
Tests for Appointment model and triage integration.
Run: pytest tests/test_appointments.py -v

FIXES APPLIED:
  - Patient.query.get(id) replaced with db.session.get(Patient, id)
  - Appointment.query.get(id) replaced with db.session.get(Appointment, id)
    (Both are deprecated since SQLAlchemy 2.0)
"""

import pytest
from datetime import datetime, timedelta
from app import create_app
from models import db as _db
from models.patient import Patient
from models.appointment import Appointment


@pytest.fixture(scope="module")
def app():
    """Create a fresh in-memory test database for the module."""
    a = create_app("testing")
    with a.app_context():
        _db.create_all()
        yield a
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="module")
def patient(app):
    """
    Create a test patient and return only their ID.
    Returning the ID (not the object) avoids DetachedInstanceError
    when the fixture is used across multiple test methods.
    """
    with app.app_context():
        p = Patient(name="Appt Test", age=30, phone="+910000000001")
        _db.session.add(p)
        _db.session.commit()
        return p.id


class TestAppointmentModel:

    def test_create_appointment(self, app, patient):
        """Booking an appointment should persist it with the given status."""
        with app.app_context():
            # FIX: use db.session.get() instead of deprecated Patient.query.get()
            p    = _db.session.get(Patient, patient)
            appt = Appointment(
                patient_id     = p.id,
                department     = "general_medicine",
                appointment_dt = datetime.utcnow() + timedelta(days=1),
                triage_level   = "NORMAL",
                status         = "confirmed",
            )
            _db.session.add(appt)
            _db.session.commit()
            assert appt.id     is not None
            assert appt.status == "confirmed"

    def test_to_dict_has_patient_name(self, app, patient):
        """to_dict() should include the patient's name (via relationship)."""
        with app.app_context():
            # FIX: use db.session.get() instead of deprecated Patient.query.get()
            p    = _db.session.get(Patient, patient)
            appt = Appointment(
                patient_id     = p.id,
                department     = "cardiology",
                appointment_dt = datetime.utcnow() + timedelta(days=2),
            )
            _db.session.add(appt)
            _db.session.commit()
            d = appt.to_dict()
            assert d["patient_name"] == "Appt Test"
            assert d["department"]   == "cardiology"

    def test_default_status_pending(self, app, patient):
        """New appointment without explicit status should default to 'pending'."""
        with app.app_context():
            appt = Appointment(
                patient_id     = patient,
                department     = "neurology",
                appointment_dt = datetime.utcnow() + timedelta(days=3),
            )
            _db.session.add(appt)
            _db.session.commit()
            assert appt.status == "pending"

    def test_default_triage_normal(self, app, patient):
        """New appointment without explicit triage should default to 'NORMAL'."""
        with app.app_context():
            appt = Appointment(
                patient_id     = patient,
                department     = "orthopedics",
                appointment_dt = datetime.utcnow() + timedelta(days=4),
            )
            _db.session.add(appt)
            _db.session.commit()
            assert appt.triage_level == "NORMAL"

    def test_status_choices(self):
        """STATUS_CHOICES must include the three main states."""
        assert "confirmed" in Appointment.STATUS_CHOICES
        assert "cancelled" in Appointment.STATUS_CHOICES
        assert "completed" in Appointment.STATUS_CHOICES

    def test_cancel_appointment(self, app, patient):
        """Changing status to 'cancelled' should persist correctly."""
        with app.app_context():
            appt = Appointment(
                patient_id     = patient,
                department     = "dermatology",
                appointment_dt = datetime.utcnow() + timedelta(days=5),
                status         = "confirmed",
            )
            _db.session.add(appt)
            _db.session.commit()

            appt.status = "cancelled"
            _db.session.commit()

            # FIX: use db.session.get() instead of deprecated Appointment.query.get()
            refreshed = _db.session.get(Appointment, appt.id)
            assert refreshed.status == "cancelled"