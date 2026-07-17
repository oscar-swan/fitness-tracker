import random
import sys
from datetime import date, timedelta
from app.utils import get_db, get_tdee_estimate, get_rec_protein, get_rec_fats, get_rec_carbs
from config import demo_characters, demo_history_days, weights_exercises, cardio_activities, activity_multiplier


def _log_day(cur, user_id, day, weight, calories, protein, carbs, fats, sleep, micros_ok):
    cur.execute(
        """INSERT INTO daily_logs
           (user_id, date, weight, calories, protein, carbs, fats, sleep, micros_ok)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, day.isoformat(), weight, calories, protein, carbs, fats, sleep, micros_ok),
    )


def _log_weights_session(cur, user_id, day, rng, fixed_exercises=None, progress=None):
    cur.execute(
        """INSERT INTO workout_sessions (user_id, date, session_type, nl_input_raw, parsed_ok)
           VALUES (?, ?, 'weights', ?, 1)""",
        (user_id, day.isoformat(), "auto-generated demo session"),
    )
    session_id = cur.lastrowid

    if fixed_exercises is not None:
        for exercise, start_kg, end_kg in fixed_exercises:
            weight_kg = round(start_kg + progress * (end_kg - start_kg))
            cur.execute(
                """INSERT INTO weight_exercises
                   (session_id, exercise_name, weight_kg, sets, reps, rpe)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, exercise, weight_kg,
                 rng.choice([3, 4, 5]), rng.choice([5, 6, 8, 10]), rng.choice([6, 7, 8, 9])),
            )
    else:
        for exercise in rng.sample(weights_exercises, k=3):
            cur.execute(
                """INSERT INTO weight_exercises
                   (session_id, exercise_name, weight_kg, sets, reps, rpe)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, exercise, rng.choice([40, 50, 60, 70, 80, 100]),
                 rng.choice([3, 4, 5]), rng.choice([5, 6, 8, 10]), rng.choice([6, 7, 8, 9])),
            )


def _log_cardio_session(cur, user_id, day, rng):
    cur.execute(
        """INSERT INTO workout_sessions (user_id, date, session_type, nl_input_raw, parsed_ok)
           VALUES (?, ?, 'cardio', ?, 1)""",
        (user_id, day.isoformat(), "auto-generated demo session"),
    )
    session_id = cur.lastrowid
    duration = rng.choice([20, 30, 40, 45, 60])
    cur.execute(
        """INSERT INTO cardio_sessions (session_id, activity, duration_minutes, distance_km)
           VALUES (?, ?, ?, ?)""",
        (session_id, rng.choice(cardio_activities), duration, round(duration / 6, 1)),
    )


def macro_targets(calories, weight, goal):
    """Splits a day's calories into protein/carbs/fats using the same
    rec_* helpers the rest of the app uses, so demo data matches what a
    real user would be shown for the same goal."""
    protein = get_rec_protein(goal, weight)
    fats = get_rec_fats(calories, goal)
    carbs = get_rec_carbs(calories, protein, fats)
    return protein, carbs, fats


def generate_hypertrophy_on_track(cur, user_id, stats, cal_adjustment, rng):
    tdee = get_tdee_estimate(
        stats["gender"], stats["weight"], stats["height"], stats["age"],
        stats["bf_category"], stats["muscle_category"], activity_multiplier,
    )
    target = tdee + 300 + cal_adjustment
    weight = stats["weight"] - 1.2
    today = date.today()

    core_lifts = rng.sample(weights_exercises, k=3)
    lift_progressions = [(lift, 40, 60) for lift in core_lifts]

    for i in range(demo_history_days, 0, -1):
        day = today - timedelta(days=i)
        weight += rng.uniform(0.02, 0.06)
        calories = target + rng.randint(-100, 100)
        protein, carbs, fats = macro_targets(calories, weight, stats["goal"])
        _log_day(cur, user_id, day, round(weight, 1), calories, protein, carbs, fats,
                 round(rng.uniform(6.5, 8.5), 1), rng.choice([1, 1, 1, 0]))
        if day.weekday() in (0, 2, 4):
            progress = (demo_history_days - i) / demo_history_days
            _log_weights_session(cur, user_id, day, rng, lift_progressions, progress)
    cur.execute(
        """INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
           VALUES (?, ?, ?, 'calculated')""",
        (user_id, 15.5, (today - timedelta(days=2)).isoformat()),
    )


def generate_hypertrophy_stalled_undereating(cur, user_id, stats, cal_adjustment, rng):
    tdee = get_tdee_estimate(
        stats["gender"],
        stats["weight"],
        stats["height"],
        stats["age"],
        stats["bf_category"],
        stats["muscle_category"],
        activity_multiplier,
    )
    target = tdee + 300 + cal_adjustment
    actual = tdee - 100
    weight = stats["weight"]
    today = date.today()
    for i in range(demo_history_days, 0, -1):
        day = today - timedelta(days=i)
        weight += rng.uniform(-0.03, 0.03)
        calories = actual + rng.randint(-80, 80)
        protein, carbs, fats = macro_targets(calories, weight, stats["goal"])
        _log_day(cur, user_id, day, round(weight, 1), calories, protein, carbs, fats,
                 round(rng.uniform(6.0, 7.5), 1), rng.choice([1, 0, 1, 0]))
        if day.weekday() in (0, 2, 4):
            _log_weights_session(cur, user_id, day, rng)
    cur.execute(
        """INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
           VALUES (?, ?, ?, 'calculated')""",
        (user_id, 19.0, (today - timedelta(days=2)).isoformat()),
    )


def generate_fat_loss_on_track(cur, user_id, stats, cal_adjustment, rng):
    tdee = get_tdee_estimate(
        stats["gender"],
        stats["weight"],
        stats["height"],
        stats["age"],
        stats["bf_category"],
        stats["muscle_category"],
        activity_multiplier,
    )
    target = tdee - 400 + cal_adjustment
    weight = stats["weight"] + 1.5
    today = date.today()
    for i in range(demo_history_days, 0, -1):
        day = today - timedelta(days=i)
        weight -= rng.uniform(0.03, 0.08)
        calories = target + rng.randint(-100, 100)
        protein, carbs, fats = macro_targets(calories, weight, stats["goal"])
        _log_day(cur, user_id, day, round(weight, 1), calories, protein, carbs, fats,
                 round(rng.uniform(6.5, 8.0), 1), rng.choice([1, 1, 1, 0]))
        if day.weekday() in (0, 2, 4):
            _log_weights_session(cur, user_id, day, rng)
        if day.weekday() in (1, 3, 5):
            _log_cardio_session(cur, user_id, day, rng)
    cur.execute(
        """INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
           VALUES (?, ?, ?, 'calculated')""",
        (user_id, 24.0, (today - timedelta(days=2)).isoformat()),
    )


def generate_fat_loss_stalled_no_cardio(cur, user_id, stats, cal_adjustment, rng):
    tdee = get_tdee_estimate(
        stats["gender"],
        stats["weight"],
        stats["height"],
        stats["age"],
        stats["bf_category"],
        stats["muscle_category"],
        activity_multiplier,
    )
    target = tdee - 400 + cal_adjustment
    weight = stats["weight"]
    today = date.today()
    for i in range(demo_history_days, 0, -1):
        day = today - timedelta(days=i)
        weight += rng.uniform(-0.02, 0.02)
        calories = target + rng.randint(-80, 80)
        protein, carbs, fats = macro_targets(calories, weight, stats["goal"])
        _log_day(cur, user_id, day, round(weight, 1), calories, protein, carbs, fats,
                 round(rng.uniform(6.0, 8.0), 1), rng.choice([1, 1, 0]))
        if day.weekday() in (0, 2, 4):
            _log_weights_session(cur, user_id, day, rng)
    cur.execute(
        """INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
           VALUES (?, ?, ?, 'calculated')""",
        (user_id, 27.0, (today - timedelta(days=2)).isoformat()),
    )


def generate_endurance(cur, user_id, stats, cal_adjustment, rng):
    tdee = get_tdee_estimate(
        stats["gender"],
        stats["weight"],
        stats["height"],
        stats["age"],
        stats["bf_category"],
        stats["muscle_category"],
        activity_multiplier,
    )
    target = tdee + cal_adjustment
    weight = stats["weight"]
    today = date.today()
    for i in range(demo_history_days, 0, -1):
        day = today - timedelta(days=i)
        weight += rng.uniform(-0.03, 0.03)
        calories = target + rng.randint(-100, 100)
        protein, carbs, fats = macro_targets(calories, weight, stats["goal"])
        _log_day(cur, user_id, day, round(weight, 1), calories, protein, carbs, fats,
                 round(rng.uniform(7.0, 8.5), 1), rng.choice([1, 1, 1, 0]))
        if day.weekday() in (1, 3, 5, 6):
            _log_cardio_session(cur, user_id, day, rng)
    cur.execute(
        """INSERT INTO bf_calc (user_id, body_fat_percent, date, method)
           VALUES (?, ?, ?, 'calculated')""",
        (user_id, 16.0, (today - timedelta(days=2)).isoformat()),
    )


def generate_endurance_no_logging(cur, user_id, stats, cal_adjustment, rng):
    today = date.today()
    stray_days = rng.sample(range(3, demo_history_days), k=2)
    for i in stray_days:
        day = today - timedelta(days=i)
        _log_cardio_session(cur, user_id, day, rng)


GENERATORS = {
    "Hypertrophy, on track to goal": generate_hypertrophy_on_track,
    "Hypertrophy, several issues": generate_hypertrophy_stalled_undereating,
    "Fat loss, eats too many calories": generate_fat_loss_on_track,
    "Fat loss, not doing enough cardio": generate_fat_loss_stalled_no_cardio,
    "Endurance, does not eat micronutrients or work out hard enough": generate_endurance,
    "Endurance, does not log data": generate_endurance_no_logging,
}


def reset_demo_character(user_id):
    """Wipes every row belonging to this demo user_id across all tables,
    but leaves the row for other demo users untouched. Safe to call even
    if the user has never been seeded before."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM weight_exercises WHERE session_id IN "
        "(SELECT session_id FROM workout_sessions WHERE user_id = ?)",
        (user_id,),
    )
    cur.execute(
        "DELETE FROM cardio_sessions WHERE session_id IN "
        "(SELECT session_id FROM workout_sessions WHERE user_id = ?)",
        (user_id,),
    )
    cur.execute("DELETE FROM workout_sessions WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM daily_logs WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM bf_calc WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM user_stats WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def seed_demo_character(user_id, char):
    stats = char["stats"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (user_id, email, password, is_demo, created_at) VALUES (?, ?, ?, 1, ?)",
        (
            user_id,
            f"demo{user_id}@demo.local",
            None,
            (date.today() - timedelta(days=demo_history_days)).isoformat(),
        ),
    )

    cur.execute(
        """INSERT INTO user_stats
           (user_id, height, weight, age, gender, goal, goal_set_date,
            experience, bf_category, muscle_category, calorie_adjustment, cal_adjustment_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, stats["height"], stats["weight"], stats["age"], stats["gender"],
            stats["goal"], (date.today() - timedelta(days=demo_history_days)).isoformat(),
            "intermediate", stats["bf_category"], stats["muscle_category"],
            char["cal_adjustment"], date.today().isoformat(),
        ),
    )
    conn.commit()

    generator = GENERATORS.get(char["demo_type"])
    if generator is None:
        conn.close()
        raise ValueError(
            f"No history generator registered for demo_type {char['demo_type']!r} "
            f"(user_id {user_id}). Add one to GENERATORS."
        )

    rng = random.Random(user_id)  # seeded per-character so runs are reproducible
    generator(cur, user_id, stats, char["cal_adjustment"], rng)
    conn.commit()
    conn.close()


def reset_and_seed_character(user_id):
    reset_demo_character(user_id)
    seed_demo_character(user_id, demo_characters[user_id])


def reset_and_seed_all():
    for user_id, char in demo_characters.items():
        reset_demo_character(user_id)
        seed_demo_character(user_id, char)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "seed":
        reset_and_seed_all()
        print(f"Seeded {len(demo_characters)} demo characters.")

    elif command == "reset":
        if len(sys.argv) < 3:
            print("Usage: python seed.py reset <user_id|all>")
            sys.exit(1)
        target = sys.argv[2]
        if target == "all":
            reset_and_seed_all()
            print("All demo characters reset to default.")
        else:
            uid = int(target)
            if uid not in demo_characters:
                print(f"No demo character with id {uid}")
                sys.exit(1)
            reset_and_seed_character(uid)
            print(
                f"Demo character {uid} ({demo_characters[uid].get('name') or demo_characters[uid].get('display_name')}) reset to default.")

    else:
        print(__doc__)
        sys.exit(1)