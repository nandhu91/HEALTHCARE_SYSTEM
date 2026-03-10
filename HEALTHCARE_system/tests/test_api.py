"""
tests/test_api.py
=================
Integration tests for REST API endpoints.
Run: pytest tests/test_api.py -v

FIXES APPLIED:
  - test_login_success: now relies on the session-scoped `auth_token` fixture
    which registers "testadmin" first, so the user always exists before login.
  - SQLAlchemy 2.x: Patient.query.get() replaced with db.session.get()
"""

import pytest
from app import create_app
from models import db as _db


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Create a fresh Flask app in testing mode for the whole test session."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def auth_token(client):
    """
    Register 'testadmin' then log in.
    This fixture runs ONCE for the session, so 'testadmin' always exists
    before any test that calls test_login_success.
    """
    client.post("/api/auth/register", json={
        "username": "testadmin",
        "email":    "admin@test.com",
        "password": "password123",
        "role":     "admin",
    })
    resp = client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "password123",
    })
    return resp.get_json()["token"]


@pytest.fixture(scope="session")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def sample_patient(client, headers):
    """Create and return a patient dict used across appointment/triage tests."""
    resp = client.post("/api/patients/", json={
        "name":   "Test Patient",
        "age":    35,
        "phone":  "+919876543210",
        "email":  "patient@test.com",
        "gender": "male",
    }, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()


# ── Auth tests ─────────────────────────────────────────────────────────────────

class TestAuth:

    def test_register_success(self, client):
        """Register a brand-new user — should return 201 with a token."""
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "email":    "new@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 201
        assert "token" in resp.get_json()

    def test_register_duplicate_username(self, client):
        """Registering the same username twice should return 409 Conflict."""
        client.post("/api/auth/register", json={
            "username": "dupuser", "email": "a@test.com", "password": "p"
        })
        resp = client.post("/api/auth/register", json={
            "username": "dupuser", "email": "b@test.com", "password": "p"
        })
        assert resp.status_code == 409

    def test_login_success(self, client, auth_token):
        """
        FIX: 'testadmin' is created by the session-scoped auth_token fixture.
        We simply log in again here — user already exists, so we get 200.
        """
        resp = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "token" in resp.get_json()

    def test_login_wrong_password(self, client, auth_token):
        """Wrong password must return 401."""
        resp = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_protected_route_without_token(self, client):
        """Hitting a protected endpoint without a token should return 401."""
        resp = client.get("/api/patients/")
        assert resp.status_code == 401

    def test_me_returns_user(self, client, headers):
        """/api/auth/me should return the currently logged-in user."""
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "testadmin"


# ── Patient tests ──────────────────────────────────────────────────────────────

class TestPatients:

    def test_create_patient(self, sample_patient):
        assert sample_patient["name"]  == "Test Patient"
        assert sample_patient["phone"] == "+919876543210"

    def test_list_patients(self, client, headers):
        resp = client.get("/api/patients/", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "patients" in data
        assert data["total"] >= 1

    def test_get_patient_by_id(self, client, headers, sample_patient):
        pid  = sample_patient["id"]
        resp = client.get(f"/api/patients/{pid}", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["id"] == pid

    def test_update_patient(self, client, headers, sample_patient):
        pid  = sample_patient["id"]
        resp = client.put(f"/api/patients/{pid}", json={"age": 36}, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["age"] == 36

    def test_duplicate_phone_rejected(self, client, headers, sample_patient):
        """Creating a second patient with the same phone must return 409."""
        resp = client.post("/api/patients/", json={
            "name":  "Another",
            "age":   20,
            "phone": sample_patient["phone"],
        }, headers=headers)
        assert resp.status_code == 409

    def test_get_nonexistent_patient(self, client, headers):
        resp = client.get("/api/patients/99999", headers=headers)
        assert resp.status_code == 404


# ── Appointment tests ──────────────────────────────────────────────────────────

class TestAppointments:

    def test_book_appointment(self, client, headers, sample_patient):
        resp = client.post("/api/appointments/", json={
            "patient_id":     sample_patient["id"],
            "department":     "general_medicine",
            "appointment_dt": "2099-12-01T10:00",
            "symptoms":       "headache and mild fever",
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert "appointment" in data
        assert "triage"      in data
        assert data["appointment"]["status"] == "confirmed"

    def test_triage_level_set_on_booking(self, client, headers, sample_patient):
        """Booking with red-flag symptoms must auto-classify as EMERGENCY."""
        resp = client.post("/api/appointments/", json={
            "patient_id":     sample_patient["id"],
            "department":     "cardiology",
            "appointment_dt": "2099-12-02T11:00",
            "symptoms":       "chest pain and difficulty breathing",
        }, headers=headers)
        data = resp.get_json()
        assert data["triage"]["level"] == "EMERGENCY"

    def test_list_appointments(self, client, headers):
        resp = client.get("/api/appointments/", headers=headers)
        assert resp.status_code == 200
        assert "appointments" in resp.get_json()

    def test_filter_by_status(self, client, headers):
        resp = client.get("/api/appointments/?status=confirmed", headers=headers)
        data = resp.get_json()
        for appt in data["appointments"]:
            assert appt["status"] == "confirmed"

    def test_past_date_rejected(self, client, headers, sample_patient):
        """Booking a date in the past must return 400."""
        resp = client.post("/api/appointments/", json={
            "patient_id":     sample_patient["id"],
            "department":     "general_medicine",
            "appointment_dt": "2000-01-01T10:00",
            "symptoms":       "old booking",
        }, headers=headers)
        assert resp.status_code == 400

    def test_update_appointment_status(self, client, headers, sample_patient):
        # First book a new appointment
        book = client.post("/api/appointments/", json={
            "patient_id":     sample_patient["id"],
            "department":     "orthopedics",
            "appointment_dt": "2099-12-05T09:00",
        }, headers=headers)
        appt_id = book.get_json()["appointment"]["id"]

        # Then update its status to completed
        resp = client.patch(
            f"/api/appointments/{appt_id}/status",
            json={"status": "completed"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "completed"

    def test_cancel_appointment(self, client, headers, sample_patient):
        book = client.post("/api/appointments/", json={
            "patient_id":     sample_patient["id"],
            "department":     "dermatology",
            "appointment_dt": "2099-12-10T14:00",
        }, headers=headers)
        appt_id = book.get_json()["appointment"]["id"]

        resp = client.delete(f"/api/appointments/{appt_id}", headers=headers)
        assert resp.status_code == 200

    def test_today_summary(self, client, headers):
        resp = client.get("/api/appointments/summary/today", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total"     in data
        assert "emergency" in data


# ── Triage API tests ───────────────────────────────────────────────────────────

class TestTriageAPI:

    def test_classify_normal(self, client, headers, sample_patient):
        resp = client.post("/api/triage/classify", json={
            "patient_id":    sample_patient["id"],
            "symptoms":      ["headache", "mild_cough"],
            "temperature":   99.0,
            "o2_saturation": 97.0,
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["result"]["level"] == "NORMAL"

    def test_classify_emergency(self, client, headers, sample_patient):
        resp = client.post("/api/triage/classify", json={
            "patient_id":    sample_patient["id"],
            "symptoms":      ["chest_pain"],
            "temperature":   104.5,
            "o2_saturation": 88.0,
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["result"]["level"] == "EMERGENCY"

    def test_classify_from_text(self, client, headers, sample_patient):
        """Passing symptoms as a text string should also detect EMERGENCY."""
        resp = client.post("/api/triage/classify", json={
            "patient_id":    sample_patient["id"],
            "symptoms_text": "patient has chest pain",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["result"]["level"] == "EMERGENCY"

    def test_missing_patient_id(self, client, headers):
        """Omitting patient_id must return 400 Bad Request."""
        resp = client.post("/api/triage/classify", json={
            "symptoms": ["headache"]
        }, headers=headers)
        assert resp.status_code == 400

    def test_triage_logs_endpoint(self, client, headers):
        resp = client.get("/api/triage/logs", headers=headers)
        assert resp.status_code == 200
        assert "logs" in resp.get_json()

    def test_triage_stats(self, client, headers):
        resp = client.get("/api/triage/stats", headers=headers)
        data = resp.get_json()
        assert "total"     in data
        assert "emergency" in data
        assert "normal"    in data


# ── Notification tests ─────────────────────────────────────────────────────────

class TestNotifications:

    def test_list_notifications(self, client, headers):
        resp = client.get("/api/notifications/", headers=headers)
        assert resp.status_code == 200
        assert "notifications" in resp.get_json()

    def test_unread_count(self, client, headers):
        resp = client.get("/api/notifications/unread-count", headers=headers)
        data = resp.get_json()
        assert "unread" in data
        assert "urgent" in data