#Dashboard and achievements
from flask import Blueprint, render_template, redirect, session
from app.alerts import collect_alert_data, manual_feedback
from app.utils import get_training_plan, get_current_weight, get_current_bf, get_bmi, get_lean_body_mass, get_db, \
    get_diet_rec, get_goal, get_avg_sleep, get_avg_weekly_weight_change, get_avg_weekly_bf_change
from config import goal_display_names

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():

    #Checks if user needs to be redirected
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    cursor = db.cursor()
    has_set_up_account = cursor.execute(
        "SELECT * FROM user_stats WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    if not has_set_up_account:
        return redirect("/userinfo")

    #Gets data to be displayed on dashboard
    data = collect_alert_data()
    alert = manual_feedback(data)
    diet_rec = get_diet_rec()
    rec_calories = diet_rec["calories"]
    rec_protein = diet_rec["protein"]
    rec_carbs =  diet_rec["carbs"]
    rec_fats =  diet_rec["fats"]
    training_plan = get_training_plan()
    weight = get_current_weight()
    bf = get_current_bf()
    bmi = get_bmi()
    lean_mass = get_lean_body_mass(weight, bf)
    goal = get_goal()
    goal = goal_display_names[goal]
    avg_sleep = get_avg_sleep()
    weight_change = get_avg_weekly_weight_change()
    bf_change = get_avg_weekly_bf_change()

    #Updates users current weight in user_stats table
    if weight is not None:
        cursor.execute(
            """
            UPDATE user_stats
            SET weight = ?
            WHERE user_id = ?
            """,
            (weight, session["user_id"])
        )
        db.commit()
    db.close()

    return render_template("dashboard.html", alert=alert, rec_calories=rec_calories, rec_protein=rec_protein, rec_carbs=rec_carbs, rec_fats=rec_fats, training_plan=training_plan, weight=weight, bf=bf, lean_mass=lean_mass, bmi=bmi, goal=goal, avg_sleep=avg_sleep, bf_change=bf_change, weight_change=weight_change)
