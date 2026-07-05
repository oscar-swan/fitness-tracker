import sqlite3
from app.utils import get_db


def init_db():
    """
    Create all tables if they don't already exist.
    Safe to call on every app startup — won't overwrite existing data.
    """
    conn = get_db()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # USERS
    # Login credential is email. Password is bcrypt hashed, never plain text.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            email     TEXT    UNIQUE NOT NULL,
            password  TEXT    NOT NULL,
            is_demo   INTEGER DEFAULT 0,   -- 1 for seeded demo accounts
            created_at TEXT   DEFAULT (DATE('now'))
        )
    """)

    # ------------------------------------------------------------------
    # USER STATS
    # One row per user, updated in place when the user changes their profile.
    # calorie_adjustment replaces the old cal_adjustment table.
    # cal_adjustment_date tracks when it was last changed so we don't
    # update it too often (same logic as the original, just cleaner).
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id             INTEGER PRIMARY KEY,
            height              REAL,
            weight              REAL,
            age                 INTEGER,
            gender              TEXT,
            goal                TEXT,   -- massgain | cut | fatloss | recomp |
                                        --   powerlifting | endurance
            goal_set_date       TEXT,
            experience          TEXT,   -- beginner | intermediate | advanced
            bf_category         TEXT,   -- low | medium | high (optional, for TDEE tweak)
            muscle_category     TEXT,   -- low | medium | high (optional, for TDEE tweak)
            calorie_adjustment  INTEGER DEFAULT 0,
            cal_adjustment_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ------------------------------------------------------------------
    # DAILY LOGS
    # One row per day per user. Every nutritional column is nullable —
    # the user may only fill in some fields. The system should never
    # break because a column is missing.
    # micros_ok: 1 = user says they ate well across vitamins/minerals that day,
    #            0 = they didn't, NULL = not answered.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            date      TEXT    NOT NULL,
            weight    REAL,
            calories  INTEGER,
            protein   REAL,
            carbs     REAL,
            fats      REAL,
            sleep     REAL,
            micros_ok INTEGER,   -- 0 / 1 / NULL
            notes     TEXT,      -- freeform, optional
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ------------------------------------------------------------------
    # WORKOUT SESSIONS
    # Replaces workout_log. One row per session.
    # nl_input_raw stores exactly what the user typed, always.
    # parsed_ok: 1 if Claude successfully extracted structured data,
    #            0 if the input was too vague to parse meaningfully.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            date          TEXT    NOT NULL,
            session_type  TEXT,       -- weights | cardio | both | rest
            nl_input_raw  TEXT,       -- raw text the user typed
            parsed_ok     INTEGER,    -- 0 or 1
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ------------------------------------------------------------------
    # WEIGHT EXERCISES
    # One row per exercise per session. All fields nullable — if the user
    # types "bench pressed 80kg" without sets/reps, weight_kg is saved
    # and sets/reps stay NULL. Claude still has something to work with.
    # rpe (Rate of Perceived Exertion, 1-10) is optional but useful for
    # advanced users who want to track effort level.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_exercises (
            exercise_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            exercise_name TEXT,
            weight_kg     REAL,
            sets          INTEGER,
            reps          INTEGER,
            rpe           REAL,   -- 1-10, optional
            FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id)
        )
    """)

    # ------------------------------------------------------------------
    # CARDIO SESSIONS
    # Distance replaces intensity — pace can be derived from distance + duration
    # and is more meaningful. All nullable for the same reasons as above.
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cardio_sessions (
            cardio_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id       INTEGER NOT NULL,
            activity         TEXT,   -- running | cycling | rowing | swimming | walking etc.
            duration_minutes REAL,
            distance_km      REAL,
            FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id)
        )
    """)

    # ------------------------------------------------------------------
    # BODY FAT CALCULATOR
    # method column distinguishes between the navy tape formula result
    # and a manual override (e.g. user had a DEXA scan and enters the real number).
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bf_calc (
            bf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL,
            body_fat_percent  REAL    NOT NULL,
            date              TEXT    NOT NULL,
            method            TEXT    DEFAULT 'calculated',  -- calculated | manual
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialised successfully.")


if __name__ == "__main__":
    # Run this file directly once to create the database:
    # python db_init.py
    init_db()