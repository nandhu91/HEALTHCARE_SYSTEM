"""
app.py — MediTriage Flask Application Entry Point
"""

import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

from config import config
from models import db
from routes.auth          import auth_bp
from routes.patients      import patients_bp
from routes.appointments  import appointments_bp
from routes.triage        import triage_bp
from routes.notifications import notifications_bp


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__, static_folder="static")
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    JWTManager(app)
    Migrate(app, db)
    CORS(app)

    # Blueprints
    app.register_blueprint(auth_bp,          url_prefix="/api/auth")
    app.register_blueprint(patients_bp,      url_prefix="/api/patients")
    app.register_blueprint(appointments_bp,  url_prefix="/api/appointments")
    app.register_blueprint(triage_bp,        url_prefix="/api/triage")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    # Serve frontend
    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        return send_from_directory("static", path)

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)