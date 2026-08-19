# Fitness Tracker
AI powered fitness tracking web app built with Flask and SQLite. Logs workouts, nutrition and body metrics, with Claude AI providing personalised feedback and natural language workout entry.

**Live demo:** add link here

## Contents
- [Background](#background)
- [What this project does](#what-this-project-does)
- [Screenshots](#screenshots)
- [AI Features](#ai-features)
- [How to Run](#how-to-run)
- [Technologies Used](#technologies-used)
- [Design Decisions](#design-decisions)
- [Testing](#testing)
- [Security](#security)
- [Program in Practice](#program-in-practice)
- [Evaluation](#evaluation)
- [Potential Improvements](#potential-improvements)
- [AI Use in Development](#ai-use-in-development)

# Background
The project started as my A-Level Computer Science coursework. I have decided to revisit the idea and rewrite the original code, add new features and integrate AI features that are well suited to the concept. The core ideas and structures already exist speeding up the development process.

# What this project does
This project is a web based application that tracks the users fitness. The program calculates personalised targets to help the user reach their fitness goals. The user logs their data daily, which is stored in the database. Feedback is generated using built in algorithms and Claude AI by analysing the users progress. The user can view and understand their progress with dynamic graphs.

# Screenshots

![App Dashboard](images/appdashboard.png)
![Graph Display](images/appgraphdisplay.png)

# AI Features
* AI is used to parse user input about their workout by converting it into a JSON formatted string so the relevant data can be correctly stored in the database. (Claude Haiku 4.5)
* Information about the user and their progress is passed to AI along with a standard prompt to receive dynamic feedback on the user's progress. (Claude Sonnet 5)

# How to Run
1. Clone the repository and move into the project folder:
```bash
   git clone https://github.com/oscar-swan/fitness-tracker.git
   cd fitness-tracker
```
 
2. Create and activate a virtual environment:
```bash
   python -m venv .venv
   .venv\Scripts\activate    
```
 
3. Install dependencies:
```bash
   pip install -r requirements.txt
```
 
4. Create a `.env` file in the project root with:
```
   SECRET_KEY=your_secret_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
 
5. Run the app:
```bash
   python run.py
```

# Technologies Used
- **Python 3**
- **Flask** 
- **SQLite3**
- **Anthropic Claude API** 
  - **Claude Haiku** for natural language workout parsing
  - **Claude Sonnet** for generating personalised feedback
- **Werkzeug security** for hashing user password
- **Matplotlib**
- **HTML/CSS/Jinja2** 

# Design Decisions

A lot of these decisions carry over from my A-level project, but the original implementations had bugs or didn't hold up once I started thinking about edge cases (users switching goals midway, sparse data, etc.), so most of this was rebuilt or rethought rather than copied over.

## Database Structure

- Added a goal set date so progress towards an old goal doesn't get counted towards a new one after the user changes targets.
- Added an account creation date for the same reason.
- Claude's feedback is generated once per day and cached in the database with a date stamp, not regenerated on every page load. If feedback already exists for today, it's just pulled from the database. This keeps AI usage low and stops feedback being generated every reload and wasting tokens.

## Demo Account Feature

This new addition lets a viewer explore the app with a full log history already populated, without needing to sign up and log their data for days first.

Demo account AI feedback isn't wiped on exit like the rest of the demo data is, so people can't spam generate AI calls by resetting it repeatedly.

## AI Integration

- Workout logging: AI parses natural language input, so the app doesn't need to contain every possible exercise name in a hardcoded list, and the user can just write about their workout instead of filling in boxes.
- Feedback: AI generated feedback is more personal and intuitive than the original alert only system from my original A-level version.

## Evaluating User Progress

The hardest design decisions came from figuring out how to fairly evaluate a user's data, especially for a user with limited history or one who does not log their data consistently.

### User Information for Claude
To let Claude assess progress accurately, a summary of the user's progress is created. Claude gets its generic instructions followed by:
- User's goal
- Average weekly weight and body fat changes
- Daily averages of diet intake and sleep time
- Whether strength, cardio intensity and cardio distance are increasing, decreasing or plateauing over time
- How frequently the user logs data and completes workouts
- The date the user selected their goal, plus their height, age, gender and weight
- Their actual diet targets, and how closely they've been hitting them

### Weekly Weight Change
Uses up to the most recent 3 weeks of data:
- Finds the change between week 1→2 averages and week 2→3 averages (each week's average = mean weight per day that week), then averages the two.
- With 14–20 days of data, it's just the week 1→2 difference.
- With fewer than 14 days, it calculates average daily change and multiplies by 7.

This lets the system produce an estimate with as little as 2 days of data, while getting more accurate as more data comes in.

### Body Fat Percentage Change
Same approach as weight change, adjusted for the fact that body fat percentage is logged weekly rather than daily.

### Diet and Sleep
Both evaluated as an average over the last 7 days, to reflect recent behaviour rather than the whole history.

### Strength Progress
The hardest algorithm to get right.
- An exercise is assessed once it's been logged at least twice (if within 70 days of a new goal) or 4 times (if on the same goal for 70+ days) this trades some accuracy for being able to analyse progress sooner.
- Caps at 6 entries per exercise so only recent history is used.
- Estimates 1RM from weight and reps for each session, then compares the most recent few 1RMs against the ones before that to judge direction. This means one bad session on a bad day doesn't make the program think you are not progressing.
- The ratio of exercises progressing vs regressing gives an overall score which signals that the metric is either declining, plateauing, or progressing.

### Cardio Progress
Same logic as strength used to judge whether intensity and distance covered are consistently trending up, down or plateauing.

### Calorie Adjustment System
A stored value that nudges the user's calorie target to better match their actual individual metabolism/activity over time.

If someone is hitting their calorie target but not seeing the expected effect on weight, the adjustment value shifts based on the size of that gap. It's timestamped and can only update every 14 days, so there's enough time to actually see whether the last change worked before updating again.

### Scientific Formulas Used
- BMI
- BMR
- TDEE
- Navy body fat percentage formula
- Epley's 1RM formula
- Formulas for predicting recommended macros based on the user's info

### Testing
No formal unittests yet, but I manually tested the core algorithms using `if __name__ == "__main__"` blocks in `utils.py` before integrating them.

# Security
Found and fixed a bug during a code review where the `/demoselect` route trusted a `user_id` sent from the form with no check it was actually a demo account. Anyone could send a real user's id and it would wipe their data before failing. Fixed by validating the id is a real demo account first.

# Program in Practice
I tested the program myself acting as a user to assess how effective it is as a tool for tracking fitness progress.

### Macronutrient Logging
One thing that stood out to me was when completing a daily log, if you did not count your macronutrients perfectly you would have to guess for the form. There were days where I knew I had eaten roughly the correct amount, but did not know exactly, so I just went back to check the recommended values and entered them instead. It's hard to count your exact macronutrient values daily when diet varies. A solution to this would be adding a checkbox that allows the user to auto enter the values to satisfy their daily targets into the database, although I feel this could discourage legitimate user tracking, with users 'cheating' and checking the box without checking themselves.

### Body Fat Percentage Accuracy
I noticed my calculated body fat percentage was higher than it actually is. This is typical with the Navy body fat formula, as different people store fat differently and a one size fits all formula has some discrepancies that make it unreliable. While the value may be incorrect, tracking this value to see if it is increasing or decreasing will still be just as useful, so it is only the value itself that may appear wrong.
Without the user going to get a DEXA scan it is very hard to work out body fat percentage within a program using user data. Some adjustments could be made, such as asking the user about vascularity or abdominal visibility to attempt to refine the calculated value, although this remains difficult. Perhaps AI could be used again, using a photo of the user along with the Navy formula to refine the calculation, but users may not feel comfortable uploading photos of themselves to the program which would make this difficult (see Potential Improvements).

### Lack of Visible Goals
When looking at the dashboard I noticed I did not have anything to motivate me, such as a target or goal on screen rather than just in my head. Maybe the user could select a target weight, body fat percentage or a strength target on a particular exercise, and a progress bar could be shown on how close you are to achieving that goal, along with stats on the progress made so far, such as weight loss so far etc. The program could also look at progress speed and predict when the user will reach their goal.

### Tracking Progress Over Bulk and Cut Cycles
When viewing data, body metrics such as weight and body fat percentage are likely to change over time, going up and down over several typical bulk and cut cycles, which makes actual progress hard to view over long periods of time. Storing lean mass in the database could negate this issue, as lean mass is likely to trend upwards and hold a lot more consistently over time compared to weight.

### First Time AI Feedback
Upon logging in and submitting my first daily log I had no AI feedback. This is correct program design, as the program does not have enough data to analyse the user fully yet, although a new user might not know this, so a message indicating when they will receive their first AI feedback may be appropriate. Some issues, such as not working out or not logging days consistently enough, actually also prevent AI feedback for similar reasons to a new account, which may confuse users too if they wait the specified amount of time and then still do not receive any feedback.

# Evaluation
Overall, I believe the fitness tracker is an effective tool for assisting fitness tracking and can be used by a wide range of people of varying ages, gender and goals.
Many of the algorithms used are science based formulas and ideas, the alerts signal exact issues to a user that may not know what they are doing wrong, and the AI feedback allows for a complete analysis of user progress to ensure they are on track.
I believe beginner and intermediate users would benefit the most out of using this app, as experts could refine their decisions more effectively by understanding their own body better through years of experience, although many of the features the app provides could still be useful.
I have highlighted a few difficulties and potential improvements that could be made that would make the app more effective, but I believe the app is an effective tool in its current state and a complete product.

# Potential Improvements
- User enters a  target value that is weight, strength or body fat percentage based and progress toward the selected goal is shown
- AI could predict users strength / weight / muscle mass progress into the future
- Achievements or ranking system
- Ability to converse with the AI assistant
- Strength measured by a weight to 1RM ratio rather than just 1RM as strength appears to decrease with weight loss due to loss of leverage
- Encouraging popups and logging streaks
- Mobility goal for users attempting to regain or maintain their body mobility
- Limits in place on weight loss goals and minimum recommended calories to discourage unhealthy habits and prevent encouraging eating disorders
- Change calorie adjustment to a percentage based value so that it scales better
- Add CSRF protection on state changing forms

# AI Use in development
* The database initialiser code in db_init.py was generated by AI from an updated ERD diagram based on my original A-level project database structure, reflecting my new design decisions
* AI was used to generate code within seed.py and then edited manually to integrate into the program
* CSS within the program was generated by AI to match specific design choices, then manually tweaked to refine.
* AI was used throughout development to assist with debugging.

---

My Github link: [github.com/oscar-swan](https://github.com/oscar-swan)