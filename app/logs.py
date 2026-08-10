#Graphs and workout history
import io
import base64
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # server-side rendering, no display needed
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, jsonify, session, redirect
from app.utils import get_db, get_cutoff_date, make_line_graph
from config import graph_metrics

mydata_bp = Blueprint("mydata_bp", __name__)

@mydata_bp.route("/mydata")
def mydata():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("mydata.html")

@mydata_bp.route("/mydata/exercises")
def mydata_exercises():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT we.exercise_name AS name, 'weights' AS kind
        FROM weight_exercises we
        JOIN workout_sessions ws ON we.session_id = ws.session_id
        WHERE ws.user_id = ? AND we.exercise_name IS NOT NULL
    """, (user_id,))
    weights = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT cs.activity AS name, 'cardio' AS kind
        FROM cardio_sessions cs
        JOIN workout_sessions ws ON cs.session_id = ws.session_id
        WHERE ws.user_id = ? AND cs.activity IS NOT NULL
    """, (user_id,))
    cardio = cursor.fetchall()
    conn.close()

    exercises = [{"name": r["name"], "kind": r["kind"]} for r in weights] + \
                [{"name": r["name"], "kind": r["kind"]} for r in cardio]
    return jsonify(exercises)


# ----------------------------------------------------------------------
# Single endpoint that builds whichever graph the dropdowns asked for.
# category = diet | bodymetrics | workouts
# ----------------------------------------------------------------------
@mydata_bp.route("/mydata/graph", methods=["POST"])
def mydata_graph():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    category = request.form.get("category")
    timespan = request.form.get("timespan", "1m")
    cutoff = get_cutoff_date(timespan)

    conn = get_db()
    cursor = conn.cursor()

    diet_metrics = graph_metrics["diet"]
    body_metrics = graph_metrics["body"]

    # ---------------- DIET ----------------
    if category == "diet":
        metric = request.form.get("metric")
        if metric not in diet_metrics:
            conn.close()
            return jsonify({"error": "invalid metric"}), 400

        column, ylabel = diet_metrics[metric]
        cursor.execute(f"""
            SELECT date, {column} AS value
            FROM daily_logs
            WHERE user_id = ? AND date >= ?
            ORDER BY date ASC
        """, (user_id, cutoff))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return jsonify({"error": "no data logged for this metric yet"}), 404

        dates = [r["date"] for r in rows]
        values = [r["value"] for r in rows]
        image = make_line_graph(dates, {ylabel: values}, f"{ylabel} Over Time", ylabel)
        return jsonify({"image": image})

    # ---------------- BODY METRICS ----------------
    elif category == "bodymetrics":
        metric = request.form.get("metric")
        if metric not in body_metrics:
            conn.close()
            return jsonify({"error": "invalid metric"}), 400

        ylabel = body_metrics[metric]

        if metric == "weight":
            cursor.execute("""
                SELECT date, weight AS value
                FROM daily_logs
                WHERE user_id = ? AND date >= ? AND weight IS NOT NULL
                ORDER BY date ASC
            """, (user_id, cutoff))
        else:  # bodyfat
            cursor.execute("""
                SELECT date, body_fat_percent AS value
                FROM bf_calc
                WHERE user_id = ? AND date >= ?
                ORDER BY date ASC
            """, (user_id, cutoff))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return jsonify({"error": "no data logged for this metric yet"}), 404

        dates = [r["date"] for r in rows]
        values = [r["value"] for r in rows]
        image = make_line_graph(dates, {ylabel: values}, f"{ylabel} Over Time", ylabel)
        return jsonify({"image": image})

    # ---------------- WORKOUTS ----------------
    elif category == "workouts":
        exercise = request.form.get("exercise")
        kind = request.form.get("kind")
        if not exercise or kind not in ("weights", "cardio"):
            conn.close()
            return jsonify({"error": "invalid exercise"}), 400

        if kind == "weights":
            cursor.execute("""
                SELECT ws.date AS date, we.weight_kg AS weight_kg,
                       we.sets AS sets, we.reps AS reps
                FROM weight_exercises we
                JOIN workout_sessions ws ON we.session_id = ws.session_id
                WHERE ws.user_id = ? AND we.exercise_name = ? AND ws.date >= ?
                ORDER BY ws.date ASC
            """, (user_id, exercise, cutoff))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return jsonify({"error": "no data logged for this exercise yet"}), 404

            dates = [r["date"] for r in rows]
            weight_vals = [r["weight_kg"] for r in rows]
            image = make_line_graph(
                dates,
                {"Weight (kg)": weight_vals},
                f"{exercise} — Weight Over Time",
                "Weight (kg)",
            )
            return jsonify({"image": image})

        else:  # cardio
            cursor.execute("""
                SELECT ws.date AS date, cs.duration_minutes AS duration,
                       cs.distance_km AS distance
                FROM cardio_sessions cs
                JOIN workout_sessions ws ON cs.session_id = ws.session_id
                WHERE ws.user_id = ? AND cs.activity = ? AND ws.date >= ?
                ORDER BY ws.date ASC
            """, (user_id, exercise, cutoff))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return jsonify({"error": "no data logged for this activity yet"}), 404

            dates = [r["date"] for r in rows]
            duration_vals = [r["duration"] for r in rows]
            distance_vals = [r["distance"] for r in rows]
            image = make_line_graph(
                dates,
                {"Duration (min)": duration_vals, "Distance (km)": distance_vals},
                f"{exercise} — Duration & Distance Over Time",
                "Value",
            )
            return jsonify({"image": image})

    else:
        conn.close()
        return jsonify({"error": "invalid category"}), 400