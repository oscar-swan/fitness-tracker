from app.utils import get_db, get_days_since_goal, get_1rm, get_intensity, avg_field, get_avg_weekly_weight_change, get_avg_weekly_bf_change, get_avg, is_metric_increasing, get_diet_rec, get_macro_bounds
from config import alert_strings, weights_goals, cardio_goals, weekly_weight_change_kg, data_flags, bf_boundaries
from datetime import datetime, timedelta, date
from flask import session


def collect_alert_data():
    """Collects and formats all data required to check for account alerts"""

    #Gets the date user goal was selected
    db = get_db()
    cursor = db.cursor()

    # Check if the account was created less than 2 days ago
    cursor.execute(
        "SELECT created_at FROM users WHERE user_id = ?",
        (session["user_id"],)
    )
    row = cursor.fetchone()
    created_at = row["created_at"] if row else None

    if created_at:
        cursor.execute(
            "SELECT julianday('now') - julianday(?) AS days_since_created",
            (created_at,)
        )
        days_since_created = cursor.fetchone()["days_since_created"]
        if days_since_created < 2:
            return "NewAccount"

    cursor.execute(
        "SELECT goal_set_date, goal FROM user_stats WHERE user_id = ?",
        (session["user_id"],)
    )
    row = cursor.fetchone()
    goal_set_date = row["goal_set_date"] if row else None
    goal = row["goal"] if row else None

    #Gets the amount of daily logs the user has completed in the last 10 days
    cursor.execute(
        """
        SELECT COUNT(*) FROM daily_logs
        WHERE user_id = ? AND date >= DATE('now', '-10 days')
        """,
        (session["user_id"],)
    )
    log_count = cursor.fetchone()[0]
    if log_count <=5:
        return "NED"

    # Check for new workout sessions in the last 10 days
    cursor.execute(
        """
        SELECT session_id, session_type
        FROM workout_sessions
        WHERE user_id = ? AND date >= DATE('now', '-10 days')
        """,
        (session["user_id"],)
    )
    recent_sessions = cursor.fetchall()
    session_types = [row["session_type"] for row in recent_sessions]

    if len(recent_sessions) <= 3:
        return "NWE"
    if goal in weights_goals:
        weights_count = sum(1 for t in session_types if t in ("weights", "both"))
        if weights_count < 3:
            return "NEW"
    if goal in cardio_goals:
        cardio_count = sum(1 for t in session_types if t in ("cardio", "both"))
        if cardio_count < 3:
            return "NEC"


    #Gets weight training data
    days_since_goal = get_days_since_goal(goal_set_date)
    if days_since_goal is not None and days_since_goal >= 70:
        min_entries = 4
        date_filter = "AND ws.date >= DATE('now', '-70 days')"
    else:
        min_entries = 2
        date_filter = ""

    cursor.execute(
        f"""
           SELECT we.exercise_name
           FROM weight_exercises we
           JOIN workout_sessions ws ON we.session_id = ws.session_id
           WHERE ws.user_id = ? {date_filter}
           GROUP BY we.exercise_name
           HAVING COUNT(*) >= ?
           """,
        (session["user_id"], min_entries)
    )
    qualifying_exercises = [row["exercise_name"] for row in cursor.fetchall()]

    exercise_history = []
    for name in qualifying_exercises:
        cursor.execute(
            """
            SELECT COUNT(*) FROM weight_exercises we
            JOIN workout_sessions ws ON we.session_id = ws.session_id
            WHERE ws.user_id = ? AND we.exercise_name = ?
            """,
            (session["user_id"], name)
        )
        total_entries = cursor.fetchone()[0]

        if total_entries >= 6:
            take = 6
        elif total_entries >= 4:
            take = 4
        else:
            take = 2

        cursor.execute(
            """
            SELECT we.weight_kg, we.reps
            FROM weight_exercises we
            JOIN workout_sessions ws ON we.session_id = ws.session_id
            WHERE ws.user_id = ? AND we.exercise_name = ?
            ORDER BY ws.date DESC
            LIMIT ?
            """,
            (session["user_id"], name, take)
        )
        rows = cursor.fetchall()[::-1]  # reverse to oldest -> newest

        one_rms = [get_1rm(row["weight_kg"], row["reps"]) for row in rows]

        exercise_history.append(one_rms)

    # Gets cardio data (distance + intensity)
    if days_since_goal is not None and days_since_goal >= 70:
        min_entries_cardio = 6
        cardio_date_filter = "AND ws.date >= DATE('now', '-70 days')"
    else:
        min_entries_cardio = 2
        cardio_date_filter = ""

    cursor.execute(
        f"""
           SELECT cs.activity
           FROM cardio_sessions cs
           JOIN workout_sessions ws ON cs.session_id = ws.session_id
           WHERE ws.user_id = ? {cardio_date_filter}
           GROUP BY cs.activity
           HAVING COUNT(*) >= ?
           """,
        (session["user_id"], min_entries_cardio)
    )
    qualifying_cardio = [row["activity"] for row in cursor.fetchall()]

    distance_history = []
    intensity_history = []
    for activity in qualifying_cardio:
        cursor.execute(
            """
            SELECT COUNT(*) FROM cardio_sessions cs
            JOIN workout_sessions ws ON cs.session_id = ws.session_id
            WHERE ws.user_id = ? AND cs.activity = ?
            """,
            (session["user_id"], activity)
        )
        total_entries = cursor.fetchone()[0]

        if total_entries >= 10:
            take = 10
        elif total_entries >= 6:
            take = 6
        else:
            take = 2

        cursor.execute(
            """
            SELECT cs.distance_km, cs.duration_minutes
            FROM cardio_sessions cs
            JOIN workout_sessions ws ON cs.session_id = ws.session_id
            WHERE ws.user_id = ? AND cs.activity = ?
            ORDER BY ws.date DESC
            LIMIT ?
            """,
            (session["user_id"], activity, take)
        )
        rows = cursor.fetchall()[::-1]

        distances = [row["distance_km"] for row in rows]
        intensities = [get_intensity(row["distance_km"], row["duration_minutes"]) for row in rows]

        distance_history.append(distances)
        intensity_history.append(intensities)

    #Fetches diet and sleep values
    cursor.execute(
        """
        SELECT date, calories, protein, carbs, fats, sleep, micros_ok
        FROM daily_logs
        WHERE user_id = ? AND date >= DATE('now', '-6 days')
        ORDER BY date ASC
        """,
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    logs_by_date = {row["date"]: row for row in rows}

    avg_calories = avg_field(rows,"calories")
    avg_protein = avg_field(rows,"protein")
    avg_carbs = avg_field(rows,"carbs")
    avg_fats = avg_field(rows,"fats")
    avg_sleep = avg_field(rows,"sleep")
    avg_micros_ok = avg_field(rows,"micros_ok")

    calories_history = []
    protein_history = []
    carbs_history = []
    fats_history = []
    sleep_history = []
    micros_ok_history = []

    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        row = logs_by_date.get(day)

        calories_history.append(row["calories"] if row else avg_calories)
        protein_history.append(row["protein"] if row else avg_protein)
        carbs_history.append(row["carbs"] if row else avg_carbs)
        fats_history.append(row["fats"] if row else avg_fats)
        sleep_history.append(row["sleep"] if row else avg_sleep)
        micros_ok_history.append(row["micros_ok"] if row else avg_micros_ok)

    # Gets calorie adjustment data
    cursor.execute("""
        SELECT calorie_adjustment, cal_adjustment_date
        FROM user_stats
        WHERE user_id = ?
    """, (session["user_id"],))

    calorie_adjustment, cal_adjustment_date = cursor.fetchone()

    db.close()

    return {
        "goal_set_date": goal_set_date,
        "goal": goal,
        "exercise_history": exercise_history,
        "distance_history": distance_history,
        "intensity_history": intensity_history,
        "calories_history": calories_history,
        "protein_history": protein_history,
        "carbs_history": carbs_history,
        "fats_history": fats_history,
        "sleep_history": sleep_history,
        "micros_ok_history": micros_ok_history,
        "cal_adjustment": calorie_adjustment,
        "cal_adjustment_date": cal_adjustment_date,
        "user_id": session["user_id"]
    }


def manual_feedback(data):
    """Processes and analyses user data"""
    #Alert to refuse feedback if issue with user's consistency with data logging or working out
    alerts = []
    if data == "NewAccount":
        alerts.append(alert_strings["NewAccount"])
        return alerts
    if data == "NED":
        alerts.append(alert_strings["NED"])
        return alerts
    if data == "NWE":
        alerts.append(alert_strings["NWE"])
        return alerts
    if data == "NEW":
        alerts.append(alert_strings["NEW"])
        return alerts
    if data == "NEC":
        alerts.append(alert_strings["NEC"])
        return alerts

    #Process data for evaluation
    avg_weekly_weight_change = get_avg_weekly_weight_change()
    avg_weekly_bf_change = get_avg_weekly_bf_change()
    avg_calories = get_avg(data["calories_history"])
    avg_protein = get_avg(data["protein_history"])
    avg_carbs = get_avg(data["carbs_history"])
    avg_fats = get_avg(data["fats_history"])
    avg_micros = get_avg(data["micros_ok_history"])
    avg_sleep = get_avg(data["sleep_history"])
    strength_progress = is_metric_increasing(data["exercise_history"])
    distance_progress = is_metric_increasing(data["distance_history"])
    intensity_progress = is_metric_increasing(data["intensity_history"])
    goal = data["goal"]

    if avg_weekly_bf_change is not None:
        if avg_weekly_bf_change < bf_boundaries["upper"] and avg_weekly_bf_change > bf_boundaries["lower"]:
            bf_change = 2
        elif avg_weekly_bf_change > bf_boundaries["upper"]:
            bf_change = 3
        else:
            bf_change = 1
    else:
        bf_change = None

    #Get recommended macros ranges
    diet_rec = get_diet_rec()
    diet_boundaries = get_macro_bounds(diet_rec)

    #Checks for any major issues that make analysis difficult
    serious_flag = 0
    if avg_calories < diet_boundaries["calories"]["lower"]:
        alerts.append(alert_strings["TooLittleCals"])
        serious_flag = 1
    if avg_calories > diet_boundaries["calories"]["upper"]:
        alerts.append(alert_strings["TooManyCals"])
        serious_flag = 1
    if avg_protein < diet_boundaries["protein"]["lower"]:
        alerts.append(alert_strings["TooLittleProtein"])
        serious_flag = 1

    #Adjusts calorie adjustment value if recommended calories are not working for the user
    if serious_flag != 1:
        if avg_weekly_weight_change is not None:
            weight_bounds = weekly_weight_change_kg[goal]
            if avg_weekly_weight_change < weight_bounds["lower"]:
                discrepancy = weight_bounds["lower"] - avg_weekly_weight_change
                direction = 1
            elif avg_weekly_weight_change > weight_bounds["upper"]:
                discrepancy = avg_weekly_weight_change - weight_bounds["upper"]
                direction = -1
            else:
                discrepancy = 0
                direction = 0
            if direction != 0:
                if discrepancy < 0.15:
                    adjustment = 150
                elif discrepancy < 0.3:
                    adjustment = 200
                else:
                    adjustment = 300

                new_cal_adjustment = data["cal_adjustment"] + (direction * adjustment)
                if new_cal_adjustment != data["cal_adjustment"]:
                    cooldown_passed = (
                            data["cal_adjustment_date"] is None
                            or datetime.now() - datetime.fromisoformat(data["cal_adjustment_date"]) >= timedelta(days=14)
                    )

                    if cooldown_passed:
                        today_str = datetime.now().isoformat()

                        db = get_db()
                        cursor = db.cursor()
                        cursor.execute("""
                            UPDATE user_stats
                            SET calorie_adjustment = ?, cal_adjustment_date = ?
                            WHERE user_id = ?
                        """, (new_cal_adjustment, today_str, data["user_id"]))
                        db.commit()
                        db.close()

                        data["cal_adjustment"] = new_cal_adjustment
                        data["cal_adjustment_date"] = today_str

    #Analyses user data to spot issues

    if avg_protein > diet_boundaries["protein"]["upper"]:
        alerts.append(alert_strings["TooMuchProtein"])
    if avg_carbs < diet_boundaries["carbs"]["lower"]:
        alerts.append(alert_strings["TooLittleCarbs"])
    if avg_carbs > diet_boundaries["carbs"]["upper"]:
        alerts.append(alert_strings["TooManyCarbs"])
    if avg_fats < diet_boundaries["fats"]["lower"]:
        alerts.append(alert_strings["TooLittleFats"])
    if avg_fats > diet_boundaries["fats"]["upper"]:
        alerts.append(alert_strings["TooManyFats"])
    if avg_micros < 0.5:
        alerts.append(alert_strings["TooLittleMicros"])
    if avg_sleep < 7:
        alerts.append(alert_strings["TooLittleSleep"])

    bounds = data_flags[goal]
    if "bf" in bounds and bf_change not in bounds["bf"]:
        if 1 in bounds["bf"]:
            alerts.append(alert_strings["BfNoLossIssue"])
        else:
            alerts.append(alert_strings["BfNoGainIssue"])
    if "strength" in bounds and strength_progress not in bounds["strength"]:
        if 3 in bounds["strength"] and 2 not in bounds["strength"]:
            alerts.append(alert_strings["StrengthNoGainIssue"])
        else:
            alerts.append(alert_strings["StrengthNoMaintainIssue"])
    if "distance" in bounds and distance_progress not in bounds["distance"]:
        alerts.append(alert_strings["DistanceIssue"])
    if "intensity" in bounds and intensity_progress not in bounds["intensity"]:
        alerts.append(alert_strings["IntensityIssue"])

    if len(alerts) == 0:
        alerts.append(alert_strings["NoAlerts"])

    return alerts
