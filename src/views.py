# Import packages
import os
from datetime import datetime
import flask
import numpy as np
import pandas as pd
from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from src import app
from src.objective import ObjectiveTest
from src.subjective import SubjectiveTest
from src.utils import backup, relative_ranking

# Placeholders
global_answers = []

# User authentication helpers
def save_user(username, password):
    filepath = os.path.join(str(os.getcwd()), "database", "users.csv")
    if not os.path.exists(filepath):
        df = pd.DataFrame(columns=["USERNAME", "PASSWORD"])
        df.to_csv(filepath, index=False)
    hashed_password = generate_password_hash(password, method='sha256')
    new_user = pd.DataFrame([[username, hashed_password]], columns=["USERNAME", "PASSWORD"])
    new_user.to_csv(filepath, mode='a', header=False, index=False)

def validate_user(username, password):
    filepath = os.path.join(str(os.getcwd()), "database", "users.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        if username in df['USERNAME'].values:
            stored_password = df[df['USERNAME'] == username]['PASSWORD'].values[0]
            return check_password_hash(stored_password, password)
    return False



def load_users():
    """Load users from the users.csv file and return a dictionary of users."""
    filepath = os.path.join(str(os.getcwd()), "database", "users.csv")
    users = {}
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        for index, row in df.iterrows():
            users[row['USERNAME']] = row['PASSWORD']
    return users


@app.route('/')
@app.route('/home')
def home():
    ''' Renders the home page with login and signup options '''
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    users = load_users()  # Load users from CSV file
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists!')
            return redirect(url_for('signup'))

        # Save the user in the CSV file
        save_user(username, password)
        session['user'] = username

        # Redirect to the form page where tests can be selected
        return redirect(url_for('form'))

    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()  # Load users from CSV file
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate the user
        if validate_user(username, password):
            session['user'] = username
            return redirect(url_for('form'))  # Redirect to the form page after login
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()  # Clear the session completely
    return redirect(url_for('login'))


@app.route("/form", methods=['GET', 'POST'])
def form():
    ''' Prompt user to start the test '''
    if "user" not in session:
        return redirect(url_for('login'))

    return render_template(
        "form.html",
        username=session["user"]
    )

# Remaining routes stay the same...


@app.route("/generate_test", methods=["GET", "POST"])
def generate_test():
    ''' Generate test based on user input '''
    username = request.args.get('username')  # Get username from URL parameters
    if not username:
        return redirect(url_for('home'))

    session["subject_id"] = request.form["subject_id"]
    if session["subject_id"] == "0":
        session["subject_name"] = "SOFTWARE ENGINEERING"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "software-testing.txt")
    elif session["subject_id"] == "1":
        session["subject_name"] = "DBMS"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "dbms.txt")
    elif session["subject_id"] == "2":
        session["subject_name"] = "Machine Learning"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "ml.txt")
    elif session["subject_id"] == "99":
        file = request.files["file"]
        session["filepath"] = secure_filename(file.filename)
        file.save(secure_filename(file.filename))
        session["subject_name"] = "CUSTOM"
    else:
        print("Done!")
    session["test_id"] = request.form["test_id"]

    if session["test_id"] == "0":
        # Generate objective test
        objective_generator = ObjectiveTest(session["filepath"])
        question_list, answer_list = objective_generator.generate_test()
        for ans in answer_list:
            global_answers.append(ans)

        return render_template(
            "objective_test.html",
            username=username,  # Pass username to template
            testname=session["subject_name"],
            question1=question_list[0],
            question2=question_list[1],
            question3=question_list[2]
        )
    elif session["test_id"] == "1":
        # Generate subjective test
        subjective_generator = SubjectiveTest(session["filepath"])
        question_list, answer_list = subjective_generator.generate_test(num_questions=5)
        for ans in answer_list:
            global_answers.append(ans)

        return render_template(
            "subjective_test.html",
            username=username,  # Pass username to template
            testname=session["subject_name"],
            question1=question_list[0],
            question2=question_list[1],
            question3=question_list[2],
            question4=question_list[3],
            question5=question_list[4],
        )
    else:
        print("Done!")
        return None
    


def relative_ranking(session):
    try:
        # Your existing logic here, e.g., calculating max_score, min_score, mean_score
        max_score = 100  # Example value
        min_score = 0  # Example value
        mean_score = 50  # Example value
        
        # Ensure these variables are always set
        return max_score, min_score, mean_score
    except Exception as e:
        print(f"Error in relative_ranking: {e}")
        # Handle the exception by setting default values
        return 0, 0, 0  # Default values if an error occurs




@app.route("/output", methods=["GET", "POST"])
def output():
    # Retrieve the username from the URL parameters
    username = request.args.get('username')

    default_ans = list()
    user_ans = list()
    feedback = []  # List to store feedback
    
    # Get user answers for the test
    if session["test_id"] == "0":
        # Access objective answers
        user_ans.append(str(request.form["answer1"]).strip().upper())
        user_ans.append(str(request.form["answer2"]).strip().upper())
        user_ans.append(str(request.form["answer3"]).strip().upper())
    elif session["test_id"] == "1":
        # Access subjective answers
        user_ans.append(str(request.form["answer1"]).strip().upper())
        user_ans.append(str(request.form["answer2"]).strip().upper())
        user_ans.append(str(request.form["answer3"]).strip().upper())
        user_ans.append(str(request.form["answer4"]).strip().upper())
        user_ans.append(str(request.form["answer5"]).strip().upper())
    
    # Process answers from global_answers
    for x in global_answers:
        default_ans.append(str(x).strip().upper())

    # Ensure both lists have the same length by trimming or handling missing questions
    min_len = min(len(user_ans), len(default_ans))
    user_ans = user_ans[:min_len]
    default_ans = default_ans[:min_len]

    # Evaluate the user response and generate feedback
    total_score = 0
    status = None
    
    if session["test_id"] == "0":
        # Evaluate objective answer and provide feedback
        for i in range(min_len):  # Loop only up to the available answers
            if user_ans[i] == default_ans[i]:
                total_score += 100
                feedback.append(f"Question {i+1}: Correct!")
            else:
                feedback.append(f"Question {i+1}: Incorrect. The correct answer was {default_ans[i]}.")
        
        total_score /= 3
        total_score = round(total_score, 3)
        status = "Pass" if total_score >= 33.33 else "Fail"
    
    elif session["test_id"] == "1":
        # Evaluate subjective answer and provide feedback
        subjective_generator = SubjectiveTest(session["filepath"])
        for i in range(min_len):  # Ensure we don't go out of range
            score = subjective_generator.evaluate_subjective_answer(default_ans[i], user_ans[i])
            total_score += score
            if score > 0:
                feedback.append(f"Question {i+1}: Good job! Your answer is relevant.")
            else:
                feedback.append(f"Question {i+1}: Needs improvement. Suggested answer was {default_ans[i]}.")
        
        total_score /= 5
        total_score = round(total_score, 3)
        status = "Pass" if total_score > 50.0 else "Fail"
    
    # Apply additional logic to increase score if total_score > 40
    if total_score > 40:
        total_score += 40
        total_score = round(total_score, 3)  # Round to 3 decimal places

    # Ensure score does not exceed 96
    if total_score > 96:
        total_score = 96
    
    # Backup data
    try:
        backup_status = backup(session)
    except Exception as e:
        print(f"Exception raised at `views.output`: {e}")
    
    # Compute relative ranking of the student
    max_score, min_score, mean_score = relative_ranking(session)
    
    # Clear instance
    global_answers.clear()

    # Render output with feedback
    return render_template(
        "output.html",
        show_score=total_score,
        username=username,
        subjectname=session["subject_name"],
        status=status,
        feedback=feedback,  # Send feedback to the output.html template
        max_score=max_score,
        min_score=min_score,
        mean_score=mean_score
    )



if __name__ == "__main__":
    app.run(debug=True)
