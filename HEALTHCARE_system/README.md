## MediTriage — Smart Healthcare Appointment & Triage System

> A full-stack web application for automated patient triage, appointment booking, and real-time emergency alerts — built with Python Flask, SQLAlchemy, and Vanilla JS.

---

The system solves a real-world problem: hospitals often waste precious time manually assessing patient urgency. MediTriage uses a Python rule engine to instantly classify patients as **NORMAL** or **EMERGENCY** based on symptoms, vital signs, and age — and automatically notifies staff via SMS and email.

## Key Features

- 🩺 **Auto Triage** — Python rule engine classifies patients the moment an appointment is booked
- 📅 **Appointment Booking** — Full patient registration + appointment scheduling in one form
- 🚨 **Emergency Alerts** — Automated SMS (Twilio) and email notifications for critical cases
- 📊 **Live Dashboard** — Real-time stats, emergency queue, and today's schedule
- 🔐 **JWT Authentication** — Secure staff login with token-based auth
- 🧪 **50+ Unit Tests** — pytest coverage for triage engine, API routes, and models

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Frontend     | HTML5, CSS3, Vanilla JavaScript     |
| Backend      | Python 3, Flask, Flask-Blueprints   |
| Database     | SQLite (dev) / PostgreSQL (prod)    |
| ORM          | SQLAlchemy + Flask-Migrate          |
| Auth         | Flask-JWT-Extended                  |
| SMS Alerts   | Twilio REST API                     |
| Email Alerts | SMTP (Gmail App Password)           |
| Testing      | pytest                              |
| CORS         | Flask-CORS                          |

---

## Project Structure

```
healthcare_system/
│
├── app.py                        # Flask app factory — registers all blueprints
├── config.py                     # Dev / Testing / Production configurations
├── requirements.txt              # All Python dependencies
├── .env                          # Secret keys (not committed to Git)
├── .gitignore
├── README.md
│
├── models/
│   ├── __init__.py               # db = SQLAlchemy() initialised here
│   ├── user.py                   # Staff/admin user accounts
│   ├── patient.py                # Patient records
│   ├── doctor.py                 # Doctor profiles
│   ├── appointment.py            # Appointment bookings (links patient + doctor)
│   ├── triage_log.py             # Every triage classification is logged here
│   └── notification.py           # SMS / email / alert records
│
├── routes/
│   ├── auth.py                   # POST /api/auth/login  |  POST /api/auth/register
│   ├── patients.py               # CRUD  /api/patients/
│   ├── appointments.py           # CRUD  /api/appointments/ + status + reschedule
│   ├── triage.py                 # POST  /api/triage/classify  |  GET /api/triage/logs
│   └── notifications.py          # GET/POST /api/notifications/
│
├── services/
│   ├── triage_engine.py          # Core Python triage logic (rule-based scoring)
│   └── notification_service.py   # Twilio SMS + SMTP email helpers
│
├── tests/
│   ├── test_triage.py            # 30+ unit tests for the triage engine
│   ├── test_api.py               # Integration tests for all API endpoints
│   ├── test_patients.py          # Patient model unit tests
│   └── test_appointments.py      # Appointment model unit tests
│
└── static/
    └── index.html                # Single-page frontend (all CSS + JS inline)
```


## Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Set Up Environment Variables

Create a `.env` file in the root folder:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Email (for appointment reminders)
MAIL_USERNAME=yourname@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

> **Gmail tip:** Use an [App Password](https://myaccount.google.com/apppasswords), not your regular Gmail password.

## Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only triage engine tests
pytest tests/test_triage.py -v

# Run only API tests
pytest tests/test_api.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

---

## REST API Reference

All endpoints are prefixed with `/api`. Protected routes require a JWT token in the `Authorization: Bearer <token>` header.

## Authentication

| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| POST   | `/api/auth/register`   | Register a new staff account |
| POST   | `/api/auth/login`      | Login → returns JWT token    |
| GET    | `/api/auth/me`         | Get current logged-in user   |

**Login request body:**
```json
{
  "username": "admin",
  "password": "yourpassword"
}
```

**Login response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": 1, "username": "admin" }
}
```

---

## Patients

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| GET    | `/api/patients/`                  | List patients (paginated)|
| POST   | `/api/patients/`                  | Create a new patient     |
| GET    | `/api/patients/<id>`              | Get patient by ID        |
| PUT    | `/api/patients/<id>`              | Update patient details   |
| DELETE | `/api/patients/<id>`              | Delete patient           |
| GET    | `/api/patients/<id>/appointments` | Patient's appointments   |
| GET    | `/api/patients/<id>/triage-history` | Patient's triage logs  |

**Create patient body:**
```json
{
  "name": "Priya Sharma",
  "age": 32,
  "phone": "+919876543210",
  "email": "priya@email.com",
  "gender": "female",
  "blood_group": "B+"
}
```

---

## Appointments

| Method | Endpoint                              | Description                         |
|--------|---------------------------------------|-------------------------------------|
| GET    | `/api/appointments/`                  | List all appointments (filterable)  |
| POST   | `/api/appointments/`                  | Book appointment (runs triage auto) |
| GET    | `/api/appointments/<id>`              | Get appointment details             |
| PATCH  | `/api/appointments/<id>/status`       | Update status                       |
| PATCH  | `/api/appointments/<id>/reschedule`   | Reschedule date/time                |
| DELETE | `/api/appointments/<id>`              | Cancel appointment                  |
| GET    | `/api/appointments/summary/today`     | Today's stats summary               |

**Book appointment body:**
```json
{
  "patient_id": 1,
  "department": "cardiology",
  "appointment_dt": "2025-03-10T10:00",
  "symptoms": "chest pain and shortness of breath",
  "temperature": 99.1,
  "o2_saturation": 91,
  "age_group": "adult"
}
```

**Response includes auto-triage result:**
```json
{
  "appointment": { "id": 42, "status": "confirmed" },
  "triage": {
    "level": "EMERGENCY",
    "score": 99,
    "priority": 1
  }
}
```

---

## Triage

| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| POST   | `/api/triage/classify`    | Run triage classification manually |
| GET    | `/api/triage/logs`        | All triage logs (filterable)       |
| GET    | `/api/triage/stats`       | Emergency vs Normal counts         |

**Classify request body:**
```json
{
  "patient_id": 1,
  "symptoms": ["chest_pain", "difficulty_breathing"],
  "temperature": 103.5,
  "o2_saturation": 92,
  "age_group": "senior"
}
```

---

## Notifications

| Method | Endpoint                             | Description                  |
|--------|--------------------------------------|------------------------------|
| GET    | `/api/notifications/`                | List notifications           |
| POST   | `/api/notifications/send`            | Send a custom notification   |
| PATCH  | `/api/notifications/<id>/read`       | Mark as read                 |
| POST   | `/api/notifications/remind`          | Send appointment reminder    |
| GET    | `/api/notifications/unread-count`    | Unread + urgent count        |

---

## Triage Engine Logic

The triage engine is a Python rule-based system in `services/triage_engine.py`.

### How It Works

**Step 1 — Red-flag check (instant EMERGENCY)**

If any red-flag symptom is present, the patient is immediately classified as EMERGENCY regardless of vitals:

```
chest_pain, difficulty_breathing, unconscious, severe_bleeding,
stroke_signs, anaphylaxis, cardiac_arrest, severe_head_injury,
paralysis, seizure
```

**Step 2 — Vital sign scoring**

| Condition             | Points |
|-----------------------|--------|
| Temperature ≥ 104°F   | +3     |
| Temperature ≥ 102°F   | +1     |
| O2 saturation ≤ 90%   | +3     |
| O2 saturation ≤ 94%   | +2     |

**Step 3 — Symptom scoring**

| Symptom         | Points |
|-----------------|--------|
| High fever      | +2     |
| Severe pain     | +2     |
| Vomiting blood  | +3     |
| Confusion       | +2     |
| Fracture        | +2     |
| Dizziness       | +1     |
| Vomiting        | +1     |

**Step 4 — Age vulnerability**

| Age Group     | Points |
|---------------|--------|
| Child (< 18)  | +1     |
| Senior (60+)  | +1     |

**Step 5 — Final decision**

| Total Score | Classification |
|-------------|----------------|
| ≥ 4         | 🚨 EMERGENCY   |
| < 4         | ✅ NORMAL      |

---

## frontend Pages

The single-page frontend (`static/index.html`) includes 6 sections:

| Page            | What It Does                                               |
|-----------------|------------------------------------------------------------|
| **Dashboard**   | Live stats (total, emergency, confirmed), tables for today's schedule and emergency queue |
| **Book Appt.**  | Full patient + appointment form with auto-triage on submit |
| **Triage**      | Manual triage check with symptom checkboxes + vitals input |
| **Appointments**| Filterable list of all appointments with cancel action     |
| **Triage Logs** | History of every classification with score and reasoning   |
| **Alerts**      | Notification feed with Send Reminder and Emergency Alert modals |

> **Offline mode:** The frontend works without the Flask backend. The JS triage engine mirrors the Python logic exactly, and sample data is shown for notifications.

---

## requirements.txt

```
flask>=2.3.0
flask-sqlalchemy>=3.0.0
flask-jwt-extended>=4.5.0
flask-migrate>=4.0.0
flask-cors>=4.0.0
python-dotenv>=1.0.0
twilio>=8.0.0
pytest>=7.4.0
pytest-flask>=1.2.0
werkzeug>=2.3.0
```

---

## Security Notes

- All API routes (except `/api/auth/login` and `/api/auth/register`) require a valid JWT token
- Passwords are hashed using Werkzeug's `generate_password_hash` — never stored in plain text
- JWT tokens expire after 24 hours
- CORS is configured to allow only trusted origins in production

---

## Deployment (Production)

## Environment

Set the following in your `.env` file for production:

```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=a-very-long-random-secret
JWT_SECRET_KEY=another-very-long-random-secret
```

## Database Migration

```bash
flask db init       # Only needed once
flask db migrate -m "Initial migration"
flask db upgrade
```

## Run with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

---

