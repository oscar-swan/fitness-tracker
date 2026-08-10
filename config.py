#Contains the plan displayed for each user goal type
plans = {
        "hypertrophy": "Engaging 3-5 times a week in weight training, with a rep range of 6-10 on compound exercises and a rep range of 8-12 on isolation exercises. Compound lifts (squat, bench, deadlift, overhead press, pull-ups, rows) should form the core of training, supported by isolation work for targeted growth. Focus on progressive overload. Push-Pull-Legs split recommended.",
        "cut": "Engaging 3-5 times a week in weight training, with a rep range of 6-10 on compound exercises and a rep range of 8-12 on isolation exercises. Compound lifts (squat, bench, deadlift, overhead press, pull-ups, rows) should form the core of training, with a focus on preserving strength by lifting the same amount of weight. Cardio is recommended to speed up fat loss. Push-Pull-Legs split recommended.",
        "fat_loss": "Engaging 3-5 times a week in cardio based activities with a focus on meeting calorie goal to ensure consistent progress. Weight training (full body, compound lifts such as squat, bench, deadlift, overhead press, pull-ups, rows, with isolation work as needed) should also be used to preserve muscle mass during a fat loss period to ensure metabolism does not slow.",
        "recomp": "Engaging 3-5 times a week in weight training, with a rep range of 6-10 on compound exercises and a rep range of 8-12 on isolation exercises, with rest periods between sets tailored to individual recovery. Being precise about meeting calorie goal consistently is important. Compound lifts (squat, bench, deadlift, overhead press, pull-ups, rows) should form the core of training, supported by isolation work for targeted growth. Focus on progressive overload. Cardio in moderation is recommended to speed up results. Push-Pull-Legs split recommended.",
        "strength_gain": "Engaging 3-5 times a week in weight training, with a rep range of 1-6 on compound exercises and a rep range of 6-10 on isolation exercises, with longer rest periods between sets to allow full recovery. Focus on progressive overload by increasing weight over time. Compound lifts (squat, bench, deadlift, overhead press, pull-ups, rows) should make up the bulk of training, with isolation work used sparingly as accessory movements. Push-Pull-Legs or an Upper-Lower split recommended.",
        "endurance": "Engaging 4-6 times a week in a combination of steady-state cardio and high intensity interval training (1-2 sessions per week) to build both aerobic base and top-end capacity. Weight training is recommended 2x a week with higher rep ranges (12-15+) and shorter rest periods to help support muscular endurance.",
    }

#Contains the multiplier for TDEE adjustment based on user body composition in aim to make estimate more accurate
tdee_adjustments = {
        ("Low", "Low"): 1.00,
        ("Medium", "Low"): 0.97,
        ("High", "Low"): 0.92,
        ("Low", "Medium"): 1.04,
        ("Medium", "Medium"): 1.00,
        ("High", "Medium"): 0.95,
        ("Low", "High"): 1.10,
        ("Medium", "High"): 1.05,
        ("High", "High"): 1.02,
    }

#Protein multipliers for each goal type to calculate daily protein intake goal
protein_multipliers = {
        "hypertrophy" : 1.9, "cut" : 2.2, "fat_loss" : 1.5, "recomp" : 2, "strength_gain" : 1.8, "endurance" : 1.4
    }

#Values used to change BMR to get recommended daily calorie intake based on user goal
cal_goal_adjustments = {
    "hypertrophy" : 400, "cut" : -400, "fat_loss" : -625, "recomp" : -75, "strength_gain" : 250, "endurance" : 0
}

#Multipliers for recommended calorie intake to find what % of calorie intake should be fats
fat_pct_of_calories = {
        "hypertrophy": 0.25, "cut": 0.25, "fat_loss": 0.30,
        "recomp": 0.25, "strength_gain": 0.25, "endurance": 0.20,
    }

#Percentage of vote required to determine state of loss/gain
increasing_score_thresholds = {
    1:40 , 2:60
}

#String given to user when issue is flagged
alert_strings = {
    "NewAccount": "Alerts will appear here if you have any issues",
    "NED":"Log data more consistently", "NWE": "Workout more often",
    "NEW":"Lift weights more often", "NEC": "Do more cardio",
    "TooLittleCals": "Eat more calories",
    "TooManyCals": "Eat less calories",
    "TooLittleProtein": "Eat more protein",
    "TooMuchProtein": "Eat less protein",
    "TooLittleCarbs": "Eat more carbs",
    "TooManyCarbs": "Eat less carbs",
    "TooLittleFats": "Eat more fats",
    "TooManyFats": "Eat less fats",
    "TooLittleMicros": "Eat more micronutrients",
    "TooLittleSleep": "Aim for at least 8 hours sleep a day",
    "BfNoLossIssue": "You are not losing body fat",
    "BfNoGainIssue": "You are not gaining body fat",
    "StrengthNoGainIssue": "You are not gaining strength",
    "StrengthNoMaintainIssue": "You are not maintaining strength well",
    "DistanceIssue": "You are decreasing the distance you cover",
    "IntensityIssue": "You need to increase workout intensity",
    "NoAlerts": "You are on track to reach your goal"
}

#Sorts the different goals on type of exercise required
weights_goals = ["hypertrophy", "cut", "recomp", "strength_gain"]
cardio_goals = ["fat_loss", "endurance"]

#Multipliers used on exact recommended values to get recommended ranges
macro_tolerance = {
    "calories": {"upper": 1.075, "lower": 0.925},
    "protein": {"upper": 1.10, "lower": 0.90},
    "carbs": {"upper": 1.175, "lower": 0.875},
    "fats": {"upper": 1.225, "lower": 0.775},
}

#Values used to check if weekly weight change is in line with the goal
weekly_weight_change_kg = {
    "hypertrophy": {"upper": 0.4, "lower": 0.2},
    "strength_gain": {"upper": 0.24, "lower": 0.0},
    "cut": {"upper": -0.32, "lower": -0.56},
    "fat_loss": {"upper": -0.4, "lower": -0.8},
    "recomp": {"upper": 0.08, "lower": -0.08},
    "endurance": {"upper": 0.0, "lower": -0.08},
}

#Values used to analyse user data based on goal
data_flags = {
    "hypertrophy": {"bf": {2, 3, None}, "strength": {3}},
    "strength_gain": {"bf": {2, 3, None}, "strength": {3}},
    "cut": {"bf": {1, None}, "strength": {2, 3}},
    "fat_loss": {"bf": {1, None}},
    "recomp": {"bf": {1, None}, "strength": {2, 3}},
    "endurance": {"distance": {2, 3}, "intensity": {3}}
}

bf_boundaries= {
    "upper":0.1, "lower":-0.1
}

goal_display_names = {
    "hypertrophy": "Hypertrophy",
    "fat_loss": "Fat Loss",
    "strength_gain": "Strength Gain",
    "endurance": "Endurance",
    "recomp": "Recomp",
    "cut": "Cut"
}

#Info about each demo character
demo_characters = {
    9001: {
        "name": "Marcus",
        "demo_type": "Hypertrophy",
        "stats": {
            "height": 180, "weight": 82, "age": 24, "gender": "male",
            "bf_category": "Medium", "muscle_category": "Medium", "goal": "hypertrophy"
        },
        "cal_adjustment": 0,
    },
    9002: {
        "name": "Mildred",
        "demo_type": "Hypertrophy",
        "stats": {
            "height": 165, "weight": 58, "age": 29, "gender": "female",
            "bf_category": "Low", "muscle_category": "Low", "goal": "hypertrophy"
        },
        "cal_adjustment": 200,
    },
    9003: {
        "name": "Ken",
        "demo_type": "Fat loss",
        "stats": {
            "height": 178, "weight": 95, "age": 35, "gender": "male",
            "bf_category": "High", "muscle_category": "Medium", "goal": "fat_loss"
        },
        "cal_adjustment": 0,
    },
    9004: {
        "name": "Cornelius",
        "demo_type": "Fat loss",
        "stats": {
            "height": 170, "weight": 78, "age": 31, "gender": "male",
            "bf_category": "High", "muscle_category": "Low", "goal": "fat_loss"
        },
        "cal_adjustment": 0,
    },
    9005: {
        "name": "Sam",
        "demo_type": "Endurance",
        "stats": {
            "height": 175, "weight": 70, "age": 27, "gender": "male",
            "bf_category": "Medium", "muscle_category": "Medium", "goal": "endurance"
        },
        "cal_adjustment": 0,
    },
    9006: {
        "name": "Grover",
        "demo_type": "Endurance",
        "stats": {
            "height": 180, "weight": 69, "age": 22, "gender": "male",
            "bf_category": "Medium", "muscle_category": "Low", "goal": "endurance"
        },
        "cal_adjustment": 0,
    },
}

#How many days of data to generate for demo characters
demo_history_days = 28

#Exercises to use for demo accounts
weights_exercises = ["bench press", "squat", "deadlift", "overhead press", "barbell row"]
cardio_activities = ["running", "cycling", "rowing"]

#Activity multiplier
activity_multiplier = 1.55

#Workout types that can be logged
valid_workout_types = {"none", "weights", "cardio", "both"}

#Prompt to get claude to turn user weight lifting input into data
weights_claude_prompt = """You are a fitness data extraction assistant. The user describes a weight
training workout in free text, covering one or several exercises.

Extract each distinct exercise into a JSON array. Each object must have:
- exercise_name (string)
- weight_kg (number, convert lbs to kg if needed, null if not mentioned)
- sets (integer, null if not mentioned)
- reps (integer, null if not mentioned)
- rpe (number 1-10, null if not mentioned)

Respond with ONLY a JSON array. No markdown fences, no other text. If nothing
resembling a weights exercise is described, respond with []."""

#Prompt to get claude to turn user cardio input into data
cardio_claude_prompt = """You are a fitness data extraction assistant. The user describes cardio
activity in free text, covering one or several activities.

Extract each distinct activity into a JSON array. Each object must have:
- activity_name (string)
- distance_km (number, convert miles to km if needed, null if not mentioned)
- duration_min (number, null if not mentioned)

Respond with ONLY a JSON array. No markdown fences, no other text. If nothing
resembling cardio is described, respond with []."""

feedback_prompt = (
    "You are a personal trainer giving feedback to a client based on their tracked data. "
    "Be concise, encouraging, and specific. 3 to 5 sentences. Praise what's working, "
    "Identify the most important issue if one truly exists and recommend one specific next step. Interpret the data instead of repeating the values"
)

#Metrics used to generate user graph
graph_metrics = {
    "diet": {
        "calories": ("calories", "Calories (kcal)"),
        "protein":  ("protein", "Protein (g)"),
        "carbs":    ("carbs", "Carbs (g)"),
        "fats":     ("fats", "Fats (g)"),
        "sleep":    ("sleep", "Sleep (hrs)"),
    },
    "body": {
        "weight":  "Weight (kg)",
        "bodyfat": "Body Fat %",
    },
    "timespans": {
        "7d":  7,
        "1m":  30,
        "3m":  90,
        "1y":  365,
        "max": None,
    }
}
