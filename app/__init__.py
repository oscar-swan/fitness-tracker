from flask import Flask
from dotenv import load_dotenv
import os
from app.db_init import init_db


def create_app():
    """Builds the flask app"""
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="../static")
    app.secret_key = os.getenv("SECRET_KEY")

    init_db()

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    return app