from flask import Flask
from dotenv import load_dotenv
import os
from app.db_init import init_db
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    """Builds the flask app"""
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="../static")

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    app.secret_key = secret_key

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    init_db()
    csrf.init_app(app)

    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.data_input import forms_bp
    from app.graph_data import mydata_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(mydata_bp)

    return app