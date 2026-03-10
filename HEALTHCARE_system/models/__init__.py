from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user         import User
from .patient      import Patient
from .doctor       import Doctor
from .appointment  import Appointment
from .triage_log   import TriageLog
from .notification import Notification