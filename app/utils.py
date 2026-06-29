import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fitness_tracker.db")

def get_db():
    """Opens the database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows can be called like dictionaries (row["email"] not row[0])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn