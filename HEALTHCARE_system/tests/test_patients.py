"""
tests/test_patients.py
======================
Unit tests for the Patient model and patient-related logic.
Run: pytest tests/test_patients.py -v

FIXES APPLIED:
  - Patient.query.get(id) replaced with db.session.get(Patient, id)
    (Patient.query.get is deprecated since SQLAlchemy 2.0)
"""

import pytest
from app import create_app
from models import db as _db
from models.patient import Patient


@pytest.fixture(scope="module")
def app():
    """Spin up a fresh test database for this module."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="module")
def app_ctx(app):
    """Push the app context so all tests in this module can access the DB."""
    with app.app_context():
        yield


def make_patient(phone="+911111111111", name="Test", age=30):
    """Helper: create and commit a patient, return the object."""
    p = Patient(name=name, age=age, phone=phone)
    _db.session.add(p)
    _db.session.commit()
    return p


class TestPatientModel:

    def test_create_patient(self, app_ctx):
        """New patient should receive a database-assigned ID."""
        p = make_patient(phone="+912222222222", name="Alice", age=25)
        assert p.id   is not None
        assert p.name == "Alice"

    def test_to_dict_has_all_keys(self, app_ctx):
        """to_dict() must include every expected field."""
        p = make_patient(phone="+913333333333")
        d = p.to_dict()
        for key in ("id", "name", "age", "phone", "email", "blood_group", "created_at"):
            assert key in d, f"Missing key in to_dict(): {key}"

    def test_default_medical_history_empty(self, app_ctx):
        """medical_history should default to an empty string."""
        p = make_patient(phone="+914444444444")
        assert p.medical_history == ""

    def test_patient_repr(self, app_ctx):
        """repr() should include the patient's name for easy debugging."""
        p = make_patient(phone="+915555555555", name="Bob")
        assert "Bob" in repr(p)

    def test_query_by_phone(self, app_ctx):
        """Should be able to look up a patient by their phone number."""
        make_patient(phone="+916666666666", name="Charlie")
        found = Patient.query.filter_by(phone="+916666666666").first()
        assert found       is not None
        assert found.name  == "Charlie"

    def test_update_age(self, app_ctx):
        """Updating a field and committing should persist the change."""
        p = make_patient(phone="+917777777777", age=40)
        p.age = 41
        _db.session.commit()

        # FIX: use db.session.get() instead of deprecated Patient.query.get()
        refreshed = _db.session.get(Patient, p.id)
        assert refreshed.age == 41

    def test_delete_patient(self, app_ctx):
        """Deleting a patient should remove them from the database."""
        p   = make_patient(phone="+918888888888")
        pid = p.id
        _db.session.delete(p)
        _db.session.commit()

        # FIX: use db.session.get() instead of deprecated Patient.query.get()
        assert _db.session.get(Patient, pid) is None