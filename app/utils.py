import sqlite3
import os
import math
from datetime import datetime
from config import tdee_adjustments, protein_multipliers, plans, cal_goal_adjustments, fat_pct_of_calories, increasing_score_thresholds, macro_tolerance

DB_PATH = os.path.join(os.path.dirname(__file__), "fitness_tracker.db")

def get_db():
    """Opens the database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows can be called like dictionaries (row["email"] not row[0])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_training_plan():
    """Gives a training plan based on the user's goal"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
                SELECT goal
                FROM user_stats
                WHERE user_id = ?
            """, (session["user_id"],))

    goal = cursor.fetchone()["goal"]
    db.close()

    return plans.get(goal, "Error, goal did not match plan")

def get_diet_rec():
    """Returns dictionary of recommended daily intake for all macro nutrients"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
            SELECT goal, gender, height, weight, age, bf_category, muscle_category,
                   calorie_adjustment
            FROM user_stats
            WHERE user_id = ?
        """, (session["user_id"],))

    goal, gender, height, weight, age, bf_category, muscle_category, calorie_adjustment = cursor.fetchone()

    db.close()

    rec_calories = get_rec_calories(goal, gender, weight, height, age, bf_category, muscle_category, calorie_adjustment)
    rec_protein = get_rec_protein(goal, weight)
    rec_fats = get_rec_fats(rec_calories, goal)
    rec_carbs = get_rec_carbs(rec_calories, rec_protein, rec_fats)

    return {"calories": rec_calories, "protein": rec_protein, "fats": rec_fats, "carbs": rec_carbs}

def get_rec_protein(goal, weight):
    """Returns amount of protein user should eat daily"""
    multiplier = protein_multipliers[goal]
    rec_protein = round(weight * multiplier)

    return rec_protein

def get_rec_calories(goal, gender, weight, height, age, body_fat_cat=None, muscle_mass_cat=None, cal_adjustment=0,  activity_multiplier=1.55):
    """Returns amount of calories user should eat daily"""
    tdee = get_tdee_estimate(gender, weight, height, age, body_fat_cat, muscle_mass_cat, activity_multiplier)
    all_calorie_adjustments = cal_goal_adjustments[goal] + cal_adjustment
    rec_calories = round(tdee + all_calorie_adjustments)

    return rec_calories

def get_rec_carbs(rec_calories, rec_protein, rec_fats):
    """Returns amount of carbs user should eat daily"""
    protein_calories = rec_protein * 4
    fat_calories = rec_fats * 9
    remaining_calories = rec_calories - protein_calories - fat_calories
    rec_carbs = round(max(remaining_calories, 0) / 4)

    return rec_carbs

def get_rec_fats(rec_calories, goal):
    """Returns amount of fat user should eat daily"""
    fat_calories = rec_calories * fat_pct_of_calories[goal]
    rec_fats = round(fat_calories / 9)

    return rec_fats

def get_bmr(gender, weight, height, age):
    """Returns user BMR"""
    if gender == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    return bmr

def get_tdee_estimate(gender, weight, height, age, body_fat_cat=None, muscle_mass_cat=None, activity_multiplier=1.55):
    """Returns user TDEE, Uses extra info if available to give more accurate estimation"""
    bmr = get_bmr(gender, weight, height, age)
    tdee = bmr * activity_multiplier

    if body_fat_cat and muscle_mass_cat:
        multiplier = tdee_adjustments.get((body_fat_cat, muscle_mass_cat))
        if multiplier:
            tdee *= multiplier

    return tdee


def get_body_fat_percentage(gender, height, waist, neck, hip=None):
    """Estimates body fat % (Navy formula)"""
    if gender == "male":
        bf = (86.010 * math.log10(waist - neck) - 70.041 * math.log10(height) + 36.76)
    else:
        bf = (163.205 * math.log10(waist + hip - neck) - 97.684 * math.log10(height) - 78.387)

    return round(bf, 2)

def get_bmi():
    """Returns BMI"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT weight, height
        FROM user_stats
        WHERE user_id = ?
        """,
        (session["user_id"],)
    )
    row = cursor.fetchone()
    weight = row["weight"]
    height = row["height"]
    db.close()
    if weight is None or height is None:
        return None
    height_m = height / 100
    bmi = round(weight / (height_m ** 2), 1)
    return bmi

def get_lean_body_mass(weight, bf):
    """Returns lean body weight"""
    if weight is None or bf is None:
        return None
    return round(weight * (1 - (bf / 100)), 2)

def get_avg(lst):
    """Returns average of list"""
    filtered = [x for x in lst if x is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)

def is_increasing(lst):
    """Takes an even length list and returns True if the values are increasing"""
    half = len(lst) // 2
    older = lst[:half]
    newer = lst[half:]
    older_avg = sum(older) / len(older)
    newer_avg = sum(newer) / len(newer)
    if newer_avg > older_avg:
        return True
    else:
        return False

def get_vote_score(percentage):
    """Returns a score 1 to 3 depending on if data is increasing, plateauing or decreasing"""
    if percentage <= increasing_score_thresholds[1]:
        return 1
    elif percentage <= increasing_score_thresholds[2]:
        return 2
    else:
        return 3

def is_metric_increasing(exercises):
    """Uses a list of exercises and the 1RM history to determine if user is progressing, plateauing or losing ability"""
    if not exercises:
        return None
    true_count = 0
    false_count = 0
    for exercise in exercises:
        if is_increasing(exercise):
            true_count += 1
        else:
            false_count += 1
    total = true_count + false_count
    if total == 0:
        return None
    perc_true = (true_count / total) * 100
    return get_vote_score(perc_true)

def get_1rm(weight,reps):
    """Finds 1RM from a set"""
    if reps == 1:
        return round(weight)
    one_rm = weight * (1 + reps / 30)
    return round(one_rm)

def get_days_since_goal(goal_set_date):
    """Finds days since goal"""
    days_since_goal = (
            datetime.now() - datetime.strptime(goal_set_date, "%Y-%m-%d")
    ).days if goal_set_date else None
    return days_since_goal

def get_intensity(distance_km, duration_minutes):
    """Finds intensity (speed)"""
    if not distance_km or not duration_minutes or duration_minutes <= 0:
        return None

    intensity = round(distance_km / (duration_minutes / 60), 2)
    return intensity

def avg_field(rows, field):
    """Calculates average value for a field across a list of records"""
    if rows and field:
        values = [row[field] for row in rows]
        return get_avg(values)
    else:
        return None

def get_macro_bounds(diet_rec):
    """Returns the boundaries for each recommended macro"""
    return {
        macro: {
            "upper": diet_rec[key] * bounds["upper"],
            "lower": diet_rec[key] * bounds["lower"],
        }
        for macro, key, bounds in [
            ("calories", "calories", macro_tolerance["calories"]),
            ("protein", "protein", macro_tolerance["protein"]),
            ("carbs", "carbs", macro_tolerance["carbs"]),
            ("fats", "fats", macro_tolerance["fats"]),
        ]
    }

def get_current_weight():
    """Returns the average weight from the last 7 days."""
    from flask import session
    from datetime import date, timedelta

    db = get_db()
    cursor = db.cursor()

    window_start = date.today() - timedelta(days=7)

    cursor.execute(
        """
        SELECT AVG(weight) AS avg_weight
        FROM daily_logs
        WHERE user_id = ?
          AND date >= ?
        """,
        (session["user_id"], window_start.isoformat())
    )

    row = cursor.fetchone()
    current_weight = row["avg_weight"]

    db.close()
    return round(current_weight, 2) if current_weight is not None else None

def get_current_bf():
    """Returns the user's current body fat %"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT body_fat_percent
        FROM bf_calc
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )
    row = cursor.fetchone()
    db.close()
    if row is None:
        return None
    return row["body_fat_percent"]

def get_goal():
    """Returns the user's goal"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT goal FROM user_stats WHERE user_id = ?",
        (session["user_id"],)
    )
    row = cursor.fetchone()
    goal = row["goal"]
    db.close()
    return goal

def get_goal_set_date():
    """Returns the user's goal set date"""
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
                    SELECT goal_set_date
                    FROM user_stats
                    WHERE user_id = ?
                """, (session["user_id"],))

    row = cursor.fetchone()
    db.close()
    if row is None:
        return None
    return row["goal_set_date"]

def get_avg_weekly_weight_change():
    """Finds weekly weight change over a period of time using weekly averages if enough data"""
    from flask import session
    from datetime import date, timedelta
    goal_set_date = get_goal_set_date()
    today = date.today()
    window_start = date.fromisoformat(goal_set_date) if goal_set_date else today
    if (today - window_start).days > 20:
        window_start = today - timedelta(days=20)
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT date, weight
        FROM daily_logs
        WHERE user_id = ? AND date >= ?
        ORDER BY date ASC
        """,
        (session["user_id"], window_start.isoformat())
    )
    rows = cursor.fetchall()
    db.close()

    if not rows:
        weight_history = []
    else:
        logs_by_date = {row["date"]: row["weight"] for row in rows}

        start_date = date.fromisoformat(rows[0]["date"])
        end_date = date.fromisoformat(rows[-1]["date"])
        known_dates = sorted(logs_by_date.keys())

        weight_history = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()

            if date_str in logs_by_date:
                weight_history.append(logs_by_date[date_str])
            else:
                prev_str = max((d for d in known_dates if d < date_str), default=None)
                next_str = min((d for d in known_dates if d > date_str), default=None)

                if prev_str and next_str:
                    prev_date = date.fromisoformat(prev_str)
                    next_date = date.fromisoformat(next_str)
                    prev_val = logs_by_date[prev_str]
                    next_val = logs_by_date[next_str]

                    total_gap_days = (next_date - prev_date).days
                    days_from_prev = (current_date - prev_date).days
                    interpolated = prev_val + (next_val - prev_val) * (
                            days_from_prev / total_gap_days
                    )

                    weight_history.append(interpolated)

            current_date += timedelta(days=1)

    lst = weight_history

    if not lst or len(lst) == 1:
        return None
    if len(lst) >= 14 and len(lst) < 21:
        lst = lst[-14:]
        week1 = sum(lst[:7]) / 7
        week2 = sum(lst[7:]) / 7
        avg = week2 - week1
        return round(avg, 2)
    if len(lst) == 21:
        week1 = sum(lst[:7]) / 7
        week2 = sum(lst[7:14]) / 7
        week3 = sum(lst[14:21]) / 7
        change1 = week2 - week1
        change2 = week3 - week2
        avg = (change1 + change2) / 2
        return round(avg, 2)
    daily_change = []
    for i in range(1, len(lst)):
        daily_change.append(lst[i] - lst[i - 1])
    avg_daily_change = sum(daily_change) / len(daily_change)
    return round(avg_daily_change * 7, 2)

def get_avg_weekly_bf_change():
    """Finds weekly body fat change over a period of time using weekly averages"""
    from flask import session
    from datetime import date, timedelta

    goal_set_date = get_goal_set_date()
    today = date.today()

    # Fetches body fat % data
    bf_window_start = date.fromisoformat(goal_set_date) if goal_set_date else today
    if (today - bf_window_start).days > 28:
        bf_window_start = today - timedelta(days=28)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT date, body_fat_percent
        FROM bf_calc
        WHERE user_id = ? AND date >= ?
        ORDER BY date ASC
        """,
        (session["user_id"], bf_window_start.isoformat())
    )
    rows = cursor.fetchall()
    db.close()

    if not rows:
        bf_history = []
    else:
        bf_by_date = {row["date"]: row["body_fat_percent"] for row in rows}
        known_dates = sorted(bf_by_date.keys())

        start_date = date.fromisoformat(known_dates[0])
        end_date = date.fromisoformat(known_dates[-1])

        daily_bf = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in bf_by_date:
                daily_bf[date_str] = bf_by_date[date_str]
            else:
                prev_str = max(d for d in known_dates if d < date_str)
                next_str = min(d for d in known_dates if d > date_str)

                prev_date = date.fromisoformat(prev_str)
                next_date = date.fromisoformat(next_str)
                prev_val = bf_by_date[prev_str]
                next_val = bf_by_date[next_str]

                total_gap_days = (next_date - prev_date).days
                days_from_prev = (current_date - prev_date).days
                daily_bf[date_str] = prev_val + (next_val - prev_val) * (days_from_prev / total_gap_days)

            current_date += timedelta(days=1)

        bf_history = []
        sample_date = start_date
        while sample_date <= end_date:
            bf_history.append(daily_bf[sample_date.isoformat()])
            sample_date += timedelta(days=7)

    lst = bf_history

    if not lst or len(lst) == 1:
        return None
    changes = []
    for i in range(1, len(lst)):
        changes.append(lst[i] - lst[i - 1])
    avg = sum(changes) / len(changes)
    return round(avg, 2)

def get_avg_sleep():
    from flask import session
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT sleep
        FROM daily_logs
        WHERE user_id = ? AND date >= DATE('now', '-6 days')
        ORDER BY date ASC
        """,
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    db.close()
    avg_sleep = get_avg([row["sleep"] for row in rows])
    return round(avg_sleep, 1) if avg_sleep is not None else None

"""
if __name__ == '__main__':
    print(get_training_plan("hypertrophy"))
    print(get_diet_rec("hypertrophy", "male", 80, 182, 22, body_fat_cat="Medium", muscle_mass_cat="Medium", activity_multiplier=1.55, cal_adjustment=0))
    print(get_body_fat_percentage("male", 182, 85, 38))
    print(get_bmi(80, 182))
    print(get_lean_body_mass(80, 25))
    print(get_avg([1,2,3,4,5,6,7,8,9]))
    print(get_avg_weekly_weight_change([74.3,74.9,74.7,74.5,74.6,74.3,74.3,74.4,73.7,73.5,74.1,74.1,74.1,73.3,73.2,73.5,73.0]))
    print(get_avg_weekly_bf_change([20.3,19.2,18.4,17.6]))
    print(is_increasing([100,102,98,96,104,108]))
    print(is_metric_increasing([ [8,8,9,9] , [2,2,2,3] , [8,8,7,7] ]))
    print(get_1rm(80,8))
    print(get_macro_bounds({"calories": 2500, "protein": 150, "fats": 83, "carbs": 312}))
"""