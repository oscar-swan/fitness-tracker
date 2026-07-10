import sqlite3
import os
import math
from config import tdee_adjustments, protein_multipliers, plans, cal_goal_adjustments, fat_pct_of_calories, increasing_score_thresholds

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

def get_avg(list):
    """Returns average of list"""
    if not list:
        return None
    return sum(list) / len(list)

def get_avg_weekly_weight_change(list):
    """Finds weekly weight change over a period of time using weekly averages if enough data"""
    if not list or len(list) == 1:
        return None
    if len(list) >= 14 and len(list) < 21:
        list = list[-14:]
        week1 = sum(list[:7]) / 7
        week2 = sum(list[7:]) / 7
        avg = week2 - week1
        return round(avg, 2)
    if len(list) == 21:
        week1 = sum(list[:7]) / 7
        week2 = sum(list[7:14]) / 7
        week3 = sum(list[14:21]) / 7
        change1 = week2 - week1
        change2 = week3 - week2
        avg = (change1 + change2) / 2
        return round(avg, 2)
    daily_change = []
    for i in range(1, len(list)):
        daily_change.append(list[i] - list[i - 1])
    avg_daily_change = sum(daily_change) / len(daily_change)
    return round(avg_daily_change * 7, 2)

def get_avg_weekly_bf_change(list):
    """Finds weekly body fat change over a period of time using weekly averages"""
    if not list or len(list) == 1:
        return None
    changes = []
    for i in range(1, len(list)):
        changes.append(list[i] - list[i - 1])
    avg = sum(changes) / len(changes)
    return round(avg, 2)

def is_increasing(list):
    """Takes an even length list and returns True if the values are increasing"""
    half = len(list) // 2
    older = list[:half]
    newer = list[half:]
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
    true_count = 0
    false_count = 0
    for exercise in exercises:
        if is_increasing(exercise):
            true_count += 1
        else:
            false_count += 1
    total = true_count + false_count
    perc_true = (true_count / total) * 100
    return get_vote_score(perc_true)

def get_1rm(weight,reps):
    """Finds 1RM from a set"""
    if reps == 1:
        return round(weight)
    one_rm = weight * (1 + reps / 30)
    return round(one_rm)


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