# Personal details and forms
from flask import Blueprint, render_template, request, redirect, session
from app.utils import get_db

forms_bp = Blueprint("user_info", __name__)

VALID_GOALS = {"hypertrophy", "cut", "fat_loss", "recomp", "strength_gain", "endurance"}
VALID_GENDERS = {"male", "female"}


@forms_bp.route("/userinfo", methods=["GET", "POST"])
def userinfo():
    # Checks if user needs to be redirected
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        try:
            height = float(request.form["height"])
            weight = float(request.form["weight"])
            age = int(request.form["age"])
        except (KeyError, ValueError):
            return "Invalid height, weight, or age", 400

        gender = request.form.get("gender", "")
        goal = request.form.get("goal", "")
        bfa = request.form.get("bfa") or None
        mma = request.form.get("mma") or None

        if gender not in VALID_GENDERS or goal not in VALID_GOALS:
            return "Invalid gender or goal", 400

        # Check if user already has existing data
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (session["user_id"],))
        existing_data = cursor.fetchone()

        # Updates data if there is existing data and creates new entry if there is not
        if existing_data:
            cursor.execute("""
                UPDATE user_stats
                SET height = ?, weight = ?, age = ?, gender = ?, bf_category = ?, muscle_category = ?, goal = ?
                WHERE user_id = ?
            """, (height, weight, age, gender, bfa, mma, goal, session["user_id"]))
        else:
            cursor.execute("""
                INSERT INTO user_stats (user_id, height, weight, age, gender, bf_category, muscle_category, goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session["user_id"], height, weight, age, gender, bfa, mma, goal))
        db.commit()
        db.close()

        return redirect("/dashboard")

    # Checks if there is existing data to pre-populate the form with
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (session["user_id"],))
    user_data = cursor.fetchone()
    db.close()

    if user_data:
        height = user_data["height"]
        weight = user_data["weight"]
        age = user_data["age"]
        gender = user_data["gender"]
        bfa = user_data["bf_category"]
        mma = user_data["muscle_category"]
        goal = user_data["goal"]
    else:
        height = weight = age = gender = bfa = mma = goal = ""

    return render_template("userinfo.html", height=height, weight=weight, age=age,
                            gender=gender, bfa=bfa, mma=mma, goal=goal)