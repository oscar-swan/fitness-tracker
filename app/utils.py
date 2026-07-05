import sqlite3
import os
import math
from config import tdee_adjustments, protein_multipliers, plans, cal_goal_adjustments, fat_pct_of_calories

DB_PATH = os.path.join(os.path.dirname(__file__), "fitness_tracker.db")

def get_db():
    """Opens the database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows can be called like dictionaries (row["email"] not row[0])
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_training_plan(goal):
    """Gives a training plan based on the user's goal"""
    return plans.get(goal, "Error, goal did not match plan")

def get_diet_rec(goal, gender, weight, height, age, body_fat_cat=None, muscle_mass_cat=None, activity_multiplier=1.55, cal_adjustment=0):
    """Returns dictionary of recommended daily intake for all macro nutrients"""
    rec_calories = get_rec_calories(goal, gender, weight, height, age, body_fat_cat, muscle_mass_cat, activity_multiplier, cal_adjustment)
    rec_protein = get_rec_protein(goal, weight)
    rec_fats = get_rec_fats(rec_calories, goal)
    rec_carbs = get_rec_carbs(rec_calories, rec_protein, rec_fats)

    return {"calories": rec_calories, "protein": rec_protein, "fats": rec_fats, "carbs": rec_carbs}

def get_rec_protein(goal, weight):
    """Returns amount of protein user should eat daily"""
    multiplier = protein_multipliers[goal]
    rec_protein = round(weight * multiplier)

    return rec_protein

def get_rec_calories(goal, gender, weight, height, age, body_fat_cat=None, muscle_mass_cat=None, activity_multiplier=1.55, cal_adjustment=0):
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

def get_bmi(weight, height):
    """Returns BMI"""
    height_m = height / 100
    bmi = round(weight / (height_m ** 2), 1)
    return bmi

def get_lean_body_mass(weight, bf):
    """Returns lean body weight"""
    return round(weight * (1 - (bf / 100)), 2)

    

if __name__ == '__main__':
    print(get_training_plan("hypertrophy"))
    print(get_diet_rec("hypertrophy", "male", 80, 182, 22, body_fat_cat="Medium", muscle_mass_cat="Medium", activity_multiplier=1.55, cal_adjustment=0))
    print(get_body_fat_percentage("male", 182, 85, 38))
    print(get_bmi(80, 182))
    print(get_lean_body_mass(80, 25))