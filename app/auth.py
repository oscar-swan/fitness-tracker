from flask import Blueprint, render_template, request, redirect, session, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import get_db
from config import demo_characters
from seed import reset_and_seed_character

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def redir():
    #Redirects users to login page
    return redirect("/login")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    #Error initialised as none, changed if error occurs to display on page
    error = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        #Checks chosen username and password meet conditions
        if len(email) < 5 or "@" not in email or "." not in email:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        #Checks if email is already in use
        else:
            db = get_db()
            existing_email = db.execute(
                "SELECT user_id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing_email:
                error = "An account with that email already exists."
            #Otherwise adds user to the database
            else:
                db.execute(
                    "INSERT INTO users (email, password) VALUES (?, ?)",
                    (email, generate_password_hash(password))
                )
                db.commit()
                db.close()
                return redirect("/login")
            db.close()

    return render_template("signup.html", error=error)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        db = get_db()
        user = db.execute(
            "SELECT user_id, password FROM users WHERE email = ?", (email,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            return redirect("/dashboard")
        else:
            error = "Incorrect email or password."

    return render_template("login.html", error=error)

@auth_bp.route("/demoselect", methods=["GET", "POST"])
def demoselect():
    if request.method == "POST":
        user_id = int(request.form["user_id"])
        reset_and_seed_character(user_id)
        session["user_id"] = user_id
        session["is_demo"] = True
        return redirect("/dashboard")

    return render_template("demo.html", demo_characters=demo_characters)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")