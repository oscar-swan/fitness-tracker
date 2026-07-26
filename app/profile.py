# Personal details and forms
from flask import Blueprint, render_template, request, redirect, session
from app.utils import get_db, parse_weights_text, parse_cardio_text, valid_weight_exercise, valid_cardio_exercise, get_body_fat_percentage, bf_measurement_due
from datetime import date as date_cls
from config import valid_workout_types

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


@forms_bp.route("/dailyinfo", methods=["GET", "POST"])
def dailyinfo():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        log_date = request.form.get("date") or date_cls.today().isoformat()
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT 1 FROM daily_logs WHERE user_id = ? AND date = ?",
            (session["user_id"], log_date)
        )
        already_logged = cursor.fetchone()
        db.close()

        if already_logged:
            return redirect("/dashboard")

        try:
            weight = float(request.form["weight"]) if request.form.get("weight") else None
            calories = int(request.form["calories"]) if request.form.get("calories") else None
            protein = float(request.form["protein"]) if request.form.get("protein") else None
            carbs = float(request.form["carbs"]) if request.form.get("carbs") else None
            fats = float(request.form["fats"]) if request.form.get("fats") else None
            sleep = float(request.form["sleep"]) if request.form.get("sleep") else None
        except (KeyError, ValueError):
            return "Invalid numeric entry", 400

        micros_raw = request.form.get("micros_ok", "")
        micros_ok = int(micros_raw) if micros_raw in ("0", "1") else None

        workout_type = request.form.get("workout_type", "none")
        if workout_type not in valid_workout_types:
            return "Invalid workout type", 400

        weights_details = request.form.get("weights_details", "").strip()
        cardio_details = request.form.get("cardio_details", "").strip()

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO daily_logs
                (user_id, date, weight, calories, protein, carbs, fats, sleep, micros_ok)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], log_date, weight, calories, protein, carbs,
              fats, sleep, micros_ok))

        if workout_type != "none":
            valid_weights = []
            valid_cardio = []

            if workout_type in ("weights", "both") and weights_details:
                valid_weights = [e for e in parse_weights_text(weights_details)
                                  if valid_weight_exercise(e)]

            if workout_type in ("cardio", "both") and cardio_details:
                valid_cardio = [e for e in parse_cardio_text(cardio_details)
                                 if valid_cardio_exercise(e)]

            parsed_ok = 1 if (valid_weights or valid_cardio) else 0
            nl_input_raw = "\n---\n".join(t for t in [weights_details, cardio_details] if t)

            cursor.execute("""
                INSERT INTO workout_sessions (user_id, date, session_type, nl_input_raw, parsed_ok)
                VALUES (?, ?, ?, ?, ?)
            """, (session["user_id"], log_date, workout_type, nl_input_raw, parsed_ok))
            session_id = cursor.lastrowid

            for ex in valid_weights:
                cursor.execute("""
                    INSERT INTO weight_exercises (session_id, exercise_name, weight_kg, sets, reps, rpe)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, ex["exercise_name"], ex["weight_kg"],
                      ex.get("sets"), ex["reps"], ex.get("rpe")))

            for ex in valid_cardio:
                cursor.execute("""
                    INSERT INTO cardio_sessions (session_id, activity, duration_minutes, distance_km)
                    VALUES (?, ?, ?, ?)
                """, (session_id, ex["activity_name"], ex["duration_min"], ex["distance_km"]))

        bf_due = bf_measurement_due(session["user_id"])

        if bf_due:
            cursor.execute("SELECT height, gender FROM user_stats WHERE user_id = ?",
                           (session["user_id"],))
            stats_row = cursor.fetchone()

            if not stats_row:
                db.close()
                return "User stats not found", 400

            height = stats_row["height"]
            gender = stats_row["gender"]

            try:
                waist = float(request.form["waist"])
                neck = float(request.form["neck"])
                hip = float(request.form["hip"]) if gender == "female" else None
            except (KeyError, ValueError):
                db.close()
                return "Invalid waist, neck, or hip measurement", 400

            if gender == "female" and hip is None:
                db.close()
                return "Hip measurement required", 400

            bf_percent = get_body_fat_percentage(gender, height, waist, neck, hip)

            cursor.execute("""
                           INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
                           VALUES (?, ?, ?, ?)
                           """, (session["user_id"], bf_percent, log_date, "calculated"))

        db.commit()
        db.close()

        return redirect("/dashboard")

    bf_due = bf_measurement_due(session["user_id"])

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT gender FROM user_stats WHERE user_id = ?", (session["user_id"],))
    stats_row = cursor.fetchone()
    db.close()
    gender = stats_row["gender"] if stats_row else None

    return render_template("dailyinfo.html", date=date_cls.today().isoformat(), bf_due=bf_due, gender=gender)