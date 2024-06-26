#-----------------------------------------------------------------------
# fluentai.py
# Authors: Jessie Wang, Irene Kim, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sys
import random
from datetime import datetime
import re
import string
from openai import OpenAI
import flask
import sqlalchemy
import pytz
import auth
from req_lib import ReqLib
import numpy as np
from database import *

#-----------------------------------------------------------------------

app = flask.Flask(__name__)

Base.metadata.create_all(engine)

Session = sqlalchemy.orm.sessionmaker(bind=engine)

GPT_API_KEY = os.environ["GPT_API_KEY"]
app.secret_key = "1234567"  # hardcoded

#-----------------------------------------------------------------------
def generate_course_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choice(characters) for i in range(length))
        if check_unique_code(code):
            return code


#-----------------------------------------------------------------------

def get_gpt_response(prompt_text, user_input=""):
    if not GPT_API_KEY:
        print("GPT API key is missing", file=sys.stderr)
        return "Error: API key is missing."

    try:
        client = OpenAI(api_key=GPT_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content

    except Exception as ex:
        print("An error occurred: ", ex, file=sys.stderr)
        return "Error: An issue occurred while processing your request."

#-----------------------------------------------------------------------

# function for storing conversation
def store_conversation(
    conv_id, course_id, student_id, prompt_id, conv_text,
    score, prof_score):
    with Session() as session:
        new_conversation = Conversation(
            conv_id=conv_id,
            course_id=course_id,
            student_id=student_id,
            prompt_id=prompt_id,
            conv_text=conv_text,
            score=score,
            prof_score=prof_score,
        )
        session.add(new_conversation)
        session.commit()

#-----------------------------------------------------------------------

# function for storing student and prof info in the database
def store_userinfo(user_id, first_name, last_name, pustatus):
    with Session() as session:
        if pustatus in ("undergraduate", "graduate"):
            new_student = Student(
                student_id=user_id,
                first_name=first_name,
                last_name=last_name
            )
            session.add(new_student)
            session.commit()
        elif pustatus == "stf":
            new_prof = Professor(
                prof_id=user_id,
                first_name=first_name,
                last_name=last_name
            )
            session.add(new_prof)
            session.commit()

#-----------------------------------------------------------------------

# function for storing admin info in the database
def store_admininfo(user_id, first_name, last_name):
    with Session() as session:
        new_admin = SuperAdmin(
            admin_id=user_id,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(new_admin)
        session.commit()

#-----------------------------------------------------------------------

def delete_course(course_id):
    with Session() as session:
        try:
            # Delete associated professor entries, if any
            profs_deleted = (
                session.query(CoursesProfs)
                .filter(CoursesProfs.course_id == course_id)
                .delete()
            )
            print(
                f"Deleted {profs_deleted} professor associations for course ID {course_id}"
            )

            # Delete associated student entries, if any
            students_deleted = (
                session.query(CoursesStudents)
                .filter(CoursesStudents.course_id == course_id)
                .delete()
            )
            print(
                f"Deleted {students_deleted} student associations for course ID {course_id}"
            )

            # Try to find and delete the course itself
            course_entry_to_delete = (
                session.query(Course)
                .filter(Course.course_id == course_id)
                .one_or_none()
            )
            if course_entry_to_delete:
                session.delete(course_entry_to_delete)
                session.commit()
                print("Course deleted successfully.")
                return True

            # Not necessarily an error, but nothing was done
            print("No course found to delete.")
            session.commit()
            return False
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")  # Log the actual exception
            return False

#-----------------------------------------------------------------------

def delete_assignment(prompt_id):
    with Session() as session:
        try:
            # First, delete associated conversations for the assignment
            conversations_deleted = (
                session.query(Conversation)
                .filter(Conversation.prompt_id == prompt_id)
                .delete()
            )
            print(
                f"Deleted {conversations_deleted} conversations for prompt ID {prompt_id}"
            )

            # Now try to find and delete the assignment itself
            prompt_entry_to_delete = (
                session.query(Prompt)
                .filter(Prompt.prompt_id == prompt_id)
                .one_or_none()
            )
            if prompt_entry_to_delete:
                session.delete(prompt_entry_to_delete)
                session.commit()
                print("Assignment deleted successfully.")
                return True

            print("No assignment found to delete.")
            session.commit()
            return False
        except Exception as e:
            session.rollback()  # Roll back in case of error
            print(f"An error occurred: {e}")  # Log the actual exception
            return False

#-----------------------------------------------------------------------

def delete_prof_from_course(prof_id, course_id):
    with Session() as session:
        try:
            # Delete association between the professor and the course
            association_deleted = (
                session.query(CoursesProfs)
                .filter(
                    CoursesProfs.prof_id == prof_id,
                    CoursesProfs.course_id == course_id
                )
                .delete(synchronize_session=False)
            )

            # Commit the deletion of the course-professor association
            session.commit()

            if association_deleted:
                print(
                    f"Deleted association for professor ID {prof_id} from course ID {course_id}"
                )
            else:
                print("No association found to delete.")
                return False  # Exit early if no association was deleted

            # Check if the professor is teaching any other courses
            remaining_courses = (
                session.query(CoursesProfs)
                .filter(CoursesProfs.prof_id == prof_id)
                .first()
            )

            if not remaining_courses:
                # Delete professor if they don't teach any other courses
                prof_deleted = (
                    session.query(Professor)
                    .filter(Professor.prof_id == prof_id)
                    .delete(synchronize_session=False)
                )

                session.commit()  # Commit professor deletion

                if prof_deleted:
                    print(f"Professor ID {prof_id} deleted from the Professors table.")
                    return True

                print("Failed to delete professor from the Professors table.")
                return False

            # If remaining courses exist,
            # return True for successful deletion of association
            return True

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return False

#-----------------------------------------------------------------------

def delete_student_from_course(student_id, course_id):
    with Session() as session:
        try:
            # Delete the association between the student and the course
            association_deleted = (
                session.query(CoursesStudents)
                .filter(
                    CoursesStudents.student_id == student_id,
                    CoursesStudents.course_id == course_id,
                )
                .delete(synchronize_session=False)
            )

            session.commit()

            if association_deleted:
                print(
                    f"Deleted association for student ID {student_id} from course ID {course_id}"
                )
            else:
                print("No association found to delete.")
                return False  # Exit early if no association was deleted

            # Only delete student from students table
            # if they are not in any other courses
            remaining_courses = (
                session.query(CoursesStudents)
                .filter(CoursesStudents.student_id == student_id)
                .first()
            )

            if not remaining_courses:
                student_deleted = (
                    session.query(Student)
                    .filter(Student.student_id == student_id)
                    .delete(synchronize_session=False)
                )

                session.commit()

                if student_deleted:
                    print(f"Student ID {student_id} deleted from the Students table.")
                    return True

                print("Failed to delete student from the Students table.")
                return False

            return True

        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return False

#-----------------------------------------------------------------------

# Routes for authentication.
@app.route("/logoutapp", methods=["GET"])
def logoutapp():
    return auth.logoutapp()

@app.route("/logoutcas", methods=["GET"])
def logoutcas():
    return auth.logoutcas()

#-----------------------------------------------------------------------

@app.route("/")
@app.route("/index")
def home():
    return flask.render_template("index.html")

#-----------------------------------------------------------------------

@app.route("/login")
def login():
    username = auth.authenticate()

    # if new user, store user info in database
    user_type = check_user_type(username)

    if user_type is None:
        req_lib = ReqLib()

        req = req_lib.getJSON(req_lib.configs.USERS, uid=username)

        # get user first/last name, and pustatus from netid
        user_info = req[0]

        full_name = user_info.get("displayname")
        temp = full_name.split()
        first_name = temp[0]
        last_name = temp[-1]

        pustatus = user_info.get("pustatus")

        # store user info in corresponding table
        store_userinfo(username, first_name, last_name, pustatus)

    user_type = check_user_type(username)

    if user_type == "SuperAdmin":
        return flask.redirect(flask.url_for("admin_dashboard"))
    if user_type == "Professor":
        return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "Student":
        return flask.redirect(flask.url_for("student_dashboard"))

    return "Login Required: User must be a student, professor, or admin.", 401

#----------------------   STUDENT PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route("/student-dashboard")
def student_dashboard():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Professor":
        return flask.redirect(flask.url_for("prof_dashboard"))

    html_code = flask.render_template(
        "student-dashboard.html", username=username, user_type=user_type
    )
    return flask.make_response(html_code)

#-----------------------------------------------------------------------

@app.route("/student-all-courses")
def student_all_courses():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Professor":
        return flask.redirect(flask.url_for("prof_all_courses"))

    html_code = flask.render_template(
        "student-all-courses.html", 
        username=username,
        user_type=user_type
    )
    return flask.make_response(html_code)

#-----------------------------------------------------------------------

@app.route("/student-course/<course_id>")
def student_course(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    flask.session["course_id"] = course_id

    # get user's first name to display on dashboard
    user_type = check_user_type(username)
    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        first_name = get_student_firstname(username)
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        first_name = get_admin_firstname(username)

    return flask.render_template(
        "student-course.html",
        username=username,
        first_name=first_name,
        course_id=course_id,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/student-assignments/<course_id>")
def student_assignments(course_id):
    username = auth.authenticate()  # Assuming this retrieves student ID

    user_type = check_user_type(username)
    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    flask.session["course_id"] = course_id
    try:
        curr_asgmts, past_asgmts = get_assignments_for_student(
            username, course_id
        )
    except Exception:
        return flask.jsonify(
            {"error": "Failed to fetch assignments"}), 500
    return flask.render_template(
        "student-assignments.html",
        username=username,
        course_id=course_id,
        curr_assignments=curr_asgmts,
        past_assignments=past_asgmts,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/student-practice/<course_id>")
def student_practice(course_id):
    username = auth.authenticate()

    user_type = check_user_type(username)
    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    flask.session["course_id"] = course_id

    try:
        practice_assignments = get_practice_prompts(course_id)
    except Exception as e:
        print(f"An error occurred while getting practice assignments: {str(e)}")
        return None

    return flask.render_template(
        "student-practice.html",
        username=username,
        course_id=course_id,
        practice_assignments=practice_assignments,
    )

#-----------------------------------------------------------------------

@app.route("/student-scores/<course_id>")
def student_scores(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    flask.session["course_id"] = course_id

    scores = get_assignments_and_scores_for_student(course_id, username)

    return flask.render_template(
        "student-scores.html",
        username=username,
        course_id=course_id,
        scores=scores,
        user_type=user_type,
    )

#------------------------  PROFESSOR PAGES   ---------------------------
#-----------------------------------------------------------------------

@app.route("/prof-dashboard")
def prof_dashboard():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))

    return flask.render_template(
        "prof-dashboard.html", username=username, user_type=user_type
    )

#-----------------------------------------------------------------------


@app.route("/prof-all-courses")
def prof_all_courses():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))

    courses = get_courses()

    return flask.render_template(
        "prof-all-courses.html", 
        username=username, user_type=user_type, courses=courses
    )

#-----------------------------------------------------------------------

@app.route("/prof-course/<course_id>")
def prof_course(course_id):
    username = auth.authenticate()
    # get user's type to ensure they can access page
    # display name if correct
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))
        first_name = get_prof_firstname(username)
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))
        first_name = get_admin_firstname(username)

    flask.session["course_id"] = course_id

    # get course code for this course
    course_code = get_course_code(course_id)[0][0]

    return flask.render_template(
        "prof-course.html",
        username=username,
        first_name=first_name,
        course_id=course_id,
        course_code=course_code,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/prof-assignments/<course_id>")
def prof_assignments(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))

    flask.session["course_id"] = course_id

    return flask.render_template(
        "prof-assignments.html",
        username=username,
        course_id=course_id,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/delete-assignment/<int:prompt_id>", methods=["POST"])
def delete_assignment_click(prompt_id):
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        if delete_assignment(prompt_id):
            return flask.jsonify(
                {"message": "Assignment deleted successfully"}), 200

        return flask.jsonify(
            {"message": "Error deleting assignment"}), 200
    except Exception as e:
        return flask.jsonify({"message": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/prof-roster/<course_id>")
def prof_roster(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))

    flask.session["course_id"] = course_id

    return flask.render_template(
        "prof-roster.html", 
        username=username, course_id=course_id, user_type=user_type
    )

#-----------------------------------------------------------------------

def calculate_mean_and_median_scores(assignments):

    # Initialize lists to hold titles and scores
    assignment_names = []
    mean_ai_scores = []
    mean_prof_scores = []
    median_ai_scores = []
    median_prof_scores = []

    for prompt_id, title in assignments:
        scores = get_all_scores(prompt_id)
        ai_scores = np.array(
            [score[2] for score in scores if score[2] is not None])
        professor_scores = np.array(
            [score[3] for score in scores if score[3] is not None]
        )

        # Calculate mean and median scores
        mean_ai_score = np.mean(
            ai_scores) if ai_scores.size else None
        median_ai_score = np.median(
            ai_scores) if ai_scores.size else None
        mean_prof_score = np.mean(
            professor_scores) if professor_scores.size else None
        median_prof_score = np.median(
            professor_scores) if professor_scores.size else None

        # Append values to respective lists
        assignment_names.append(title)
        mean_ai_scores.append(mean_ai_score)
        mean_prof_scores.append(mean_prof_score)
        median_ai_scores.append(median_ai_score)
        median_prof_scores.append(median_prof_score)

    scores = {
        "assignment_names": assignment_names,
        "mean_ai_scores": mean_ai_scores,
        "mean_prof_scores": mean_prof_scores,
        "median_ai_scores": median_ai_scores,
        "median_prof_scores": median_prof_scores,
    }

    return scores

#-----------------------------------------------------------------------

@app.route("/calculate-scores/<course_id>")
def calculate_scores(course_id):
    try:
        assignments = get_assignments_for_prof(course_id)
        scores = calculate_mean_and_median_scores(assignments)
        return flask.jsonify(scores), 200
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/prof-scores/<course_id>")
def prof_scores(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("Access denied: Unauthorized access.", "error")
            # Redirect unauthorized professors to their dashboard
            return flask.redirect(flask.url_for("prof_dashboard"))

    flask.session["course_id"] = course_id

    assignments = get_assignments_for_prof(course_id)

    return flask.render_template(
        "prof-scores.html",
        username=username,
        course_id=course_id,
        assignments=assignments,
        user_type=user_type,
    )

#----------------------      ADMIN PAGES    ----------------------------
#-----------------------------------------------------------------------

@app.route("/admin-dashboard")
def admin_dashboard():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        first_name = get_admin_firstname(username)

    return flask.render_template(
        "admin-dashboard.html", username=username, first_name=first_name
    )

#-----------------------------------------------------------------------

@app.route("/admin-prof-roster")
def admin_prof_roster():
    username = auth.authenticate()

    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))

    return flask.render_template(
        "admin-prof-roster.html", username=username)

#-----------------------------------------------------------------------

@app.route("/admin-student-roster")
def admin_student_roster():
    username = auth.authenticate()

    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))

    student_list = get_student_info()

    return flask.render_template(
        "admin-student-roster.html", 
        username=username, student_list=student_list
    )

#-----------------------------------------------------------------------

@app.route("/admin-roster")
def admin_roster():
    username = auth.authenticate()

    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))

    return flask.render_template("admin-roster.html", username=username)


#------------------------   OTHER PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route("/student-conversation-history/<course_id>/<int:conv_id>")
def student_conversation_history(course_id, conv_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    flask.session["course_id"] = course_id

    conversation = get_conversation(conv_id)

    return flask.render_template(
        "student-conversation-history.html",
        username=username,
        course_id=course_id,
        conversation=conversation,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/student-assignment-chat/<course_id>/<int:prompt_id>")
def student_assignment_chat(course_id, prompt_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    # get generic instructions for course language
    language = get_language(course_id)[0][0]
    instructions = f"Please follow the previous instructions and speak to the student in {language}. Help them practice their language skills and do not ever switch to another language, even if they switch or ask you to. Pretend like you are having a conversation with them. Do not break character."

    # Check if the assignment has been completed
    if has_completed_assignment(username, prompt_id):
        # Redirect to the assignments page or a specific message page
        return flask.redirect(
            flask.url_for("student_assignments", course_id=course_id))

    flask.session["course_id"] = course_id
    flask.session["student_id"] = username
    flask.session["prompt_id"] = prompt_id
    flask.session["conversation_text"] = ""

    # Use the function from database.py to fetch the prompt
    prompt = get_prompt_by_id(prompt_id)

    if not prompt:
        # Handle cases where no prompt is found for the given ID
        return "Prompt not found", 404

    new_prompt_text = prompt.prompt_text + instructions

    # get prompt title
    title = get_prompt_title(prompt_id)[0][0]

    # Initialize prompt usage state
    flask.session["prompt_used"] = False
    # Store the initial prompt text for future use
    flask.session["prompt_text"] = new_prompt_text
    # Initialize turn count
    flask.session["turns_count"] = 0
    # Store max turns from database
    flask.session["max_turns"] = prompt.num_turns
    initial_response = get_gpt_response(new_prompt_text)
    # Render the chat page with the initial prompt data
    return flask.render_template(
        "student-assignment-chat.html",
        prompt_title=title,
        initial_data=initial_response,
        prompt=new_prompt_text,
        username=username,
        language=language,
        user_type=user_type,
        student_id=flask.session.get("student_id"),
        course_id=flask.session.get("course_id"),
        prompt_id=flask.session.get("prompt_id"),
        conversation_text=flask.session.get("conversation_text"),
    )

#-----------------------------------------------------------------------

def has_completed_assignment(student_id, prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        conversation = (
            session.query(Conversation)
            .filter_by(student_id=student_id, prompt_id=prompt_id)
            .first()
        )
        return conversation is not None

#-----------------------------------------------------------------------

@app.route("/prof-conversation-history/<course_id>/<int:conv_id>")
def conversation_history(course_id, conv_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("You are not teaching this course.", "error")
            return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("You are not teaching this course.", "error")
            return flask.redirect(flask.url_for("prof_dashboard"))

    flask.session["course_id"] = course_id

    try:
        conversation = get_conversation(conv_id)
    except Exception as e:
        print(f"An error occurred while getting conversation history: {str(e)}")
        return None

    return flask.render_template(
        "prof-conversation-history.html",
        username=username,
        course_id=course_id,
        conversation=conversation,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/prof-assignment-chat/<course_id>/<int:prompt_id>")
def prof_assignment_chat(course_id, prompt_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    if user_type == "Professor":
        if not check_prof_in_course(course_id, username):
            flask.flash("You are not teaching this course.", "error")
            return flask.redirect(flask.url_for("prof_dashboard"))
    if user_type == "SuperAdmin":
        if not check_prof_in_course(course_id, username):
            flask.flash("You are not teaching this course.", "error")
            return flask.redirect(flask.url_for("prof_dashboard"))

    flask.session["course_id"] = course_id

    # get generic instructions for course language
    language = get_language(course_id)[0][0]
    instructions = f"Please follow the previous instructions and speak to the student in {language}. Help them practice their language skills and do not ever switch to another language, even if they switch or ask you to. Pretend like you are having a conversation with them. Do not break character."

    # Use the function from database.py to fetch the prompt
    prompt = get_prompt_by_id(prompt_id)

    if not prompt:
        # Handle cases where no prompt is found for the given ID
        return "Prompt not found", 404

    new_prompt_text = prompt.prompt_text + instructions

    # get prompt title
    title = get_prompt_title(prompt_id)[0][0]

    # Initialize prompt usage state
    flask.session["prompt_used"] = False
    # Store the initial prompt text for future use
    flask.session["prompt_text"] = new_prompt_text
    # Initialize turn count
    flask.session["turns_count"] = 0
    # Store max turns from database
    flask.session["max_turns"] = prompt.num_turns
    initial_response = get_gpt_response(new_prompt_text)
    # Render the chat page with the initial prompt data
    return flask.render_template(
        "prof-assignment-chat.html",
        course_id=course_id,
        prompt_title=title,
        initial_data=initial_response,
        prompt=new_prompt_text,
        username=username,
        language=language,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/process-input", methods=["POST"])
def process_input():
    user_input = flask.request.form.get("userInput", "")
    current_content = flask.request.form.get("currentContent", "")
    student_id = flask.session.get("student_id")

    if not user_input:
        return flask.jsonify({"error": "No input provided"}), 400

    # Increment and check the turn count
    turns_count = flask.session.get("turns_count", 0) + 1
    max_turns = flask.session.get("max_turns", sys.maxsize)
    conversation_text = current_content

    if turns_count >= max_turns:
        course_id = flask.session.get("course_id")
        prompt_id = flask.session.get("prompt_id")
        score = calculate_score(conversation_text)
        conv_id = generate_unique_conv_id()
        prof_score = None

        # get feedback and append to conv history
        content = get_feedback(conversation_text, score)
        feedback = (
            "</div><div class='convo'" 
            + " style='margin-top: 30px; padding-top: 10px;'>"
            + "\n\n ---- FEEDBACK ---- \n\n"
            + content
        )
        conversation_text += feedback

        store_conversation(
            conv_id,
            course_id,
            student_id,
            prompt_id,
            conversation_text,
            score,
            prof_score,
        )

        # Clean up session
        flask.session.pop("turns_count", None)
        flask.session.pop("max_turns", None)
        flask.session.pop("conversation_text", None)

        return flask.jsonify(
            {
                "gpt_response": f"This conversation has reached its turn limit. Your score is {score}/100.",
                "score": score,
                "feedback": content,
            }
        )

    if not flask.session.get("prompt_used", False):
        # Use the stored prompt text
        prompt_text = flask.session.get("prompt_text", "")
        # Mark the prompt as used
        flask.session["prompt_used"] = True
    else:
        prompt_text = ""

    # Update the turn count in the session
    flask.session["turns_count"] = turns_count
    # Update current content
    flask.session["conversation_text"] = current_content

    response_text = get_gpt_response(prompt_text, user_input)
    return flask.jsonify({"gpt_response": response_text})

#---------------- STUDENT CHAT AND PROF CHAT  -------------------------
#-----------------------------------------------------------------------

@app.route("/process-input-ungraded", methods=["POST"])
def process_input_ungraded():
    user_input = flask.request.form.get("userInput", "")
    if not user_input:
        return flask.jsonify({"error": "No input provided"}), 400

    if not flask.session.get("prompt_used", False):
        # Use the stored prompt text
        prompt_text = flask.session.get("prompt_text", "")
        # Mark the prompt as used
        flask.session["prompt_used"] = True
    else:
        prompt_text = ""

    response_text = get_gpt_response(prompt_text, user_input)
    return flask.jsonify({"gpt_response": response_text})

#-----------------------------------------------------------------------

def generate_unique_conv_id():
    while True:
        id = random.randint(10000000, 99999999)
        if check_unique_convid(id):
            return id


def get_feedback(conversation_text, score):
    evaluation_prompt = f"""
        Please evaluate the following conversation based on the criteria that follows:
        
        Content: 
        - Student adheres to the conversation guidelines, follows instructions, and stays in the same language as the chatbot (10 points).
        - Content is relevant and appropriate to the topic and situation (10 points).
        - Student engages with multiple turns in the conversation (5 points).
        - Student has effective initiation of the conversation (2.5 points).
        - Student has proper and clear closing of the conversation (2.5 points).

        Grammar:
        - Student uses and references pronouns correctly (5 points).
        - Student has proper gender and number agreement between subjects, verbs, and objects (5 points).
        - Student accurately uses various verb forms as required (5 points).
        - Student appropriately uses verb tenses throughout the conversation (5 points).

        Vocabulary:
        - Student uses vocabulary that is suitable for the context of the conversation (10 points).

        Register:
        - Student uses appropriate language considering the relationship (peer vs. authority) and situation (10 points).

        Spelling:
        - There is correct spelling throughout the conversation (10 points).

        Additional Considerations:
        - Student demonstrates creativity and originality in responses (10 points).
        - Student is effective in engaging the chatbot to maintain a fluid conversation (10 points).

        You gave a score of {score} for the conversation below. Provide concise feedback to the student and tell them what they did well and what they can improve on based on the criteria above. In your response, don't put any headings or titles. Please only output several sentences of feedback and put no new lines in your response. 

        Conversation:
        {conversation_text}

    """
    try:
        client = OpenAI(api_key=GPT_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": evaluation_prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred while getting feedback: {str(e)}")
        return None


def calculate_score(conversation_text):
    evaluation_prompt = f"""
        Please evaluate the following conversation based on the criteria that follows:
        
        Content: 
        - Student adheres to the conversation guidelines and follows instructions (10 points).
        - Content is relevant and appropriate to the topic and situation (10 points).
        - Student engages with multiple turns in the conversation (5 points).
        - Student has effective initiation of the conversation (2.5 points).
        - Student has proper and clear closing of the conversation (2.5 points).

        Grammar:
        - Student uses and references pronouns correctly (5 points).
        - Student has proper gender and number agreement between subjects, verbs, and objects (5 points).
        - Student accurately uses various verb forms as required (5 points).
        - Student appropriately uses verb tenses throughout the conversation (5 points).

        Vocabulary:
        - Student uses vocabulary that is suitable for the context of the conversation (10 points).

        Register:
        - Student uses appropriate language considering the relationship (peer vs. authority) and situation (10 points).

        Spelling:
        - There is correct spelling throughout the conversation (10 points).

        Additional Considerations:
        - Student demonstrates creativity and originality in responses (10 points).
        - Student is effective in engaging the chatbot to maintain a fluid conversation (10 points).

        Provide a score out of 100 for the conversation below based on the criteria and point distribution. Only output a number in your response and no other words.

        Conversation:
        {conversation_text}

    """
    try:
        client = OpenAI(api_key=GPT_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": evaluation_prompt}],
        )
        # Extract the first number from the response
        content = response.choices[0].message.content.strip()
        score = int(re.search(r"\d+", content).group())
        return score
    except Exception as e:
        print(f"An error occurred while getting evaluation score: {str(e)}")
        return None

#-----------------------------------------------------------------------

@app.route("/student-practice-chat/<course_id>")
def student_practice_chat(course_id):
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
    elif user_type == "Professor":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("prof_dashboard"))
    elif user_type == "SuperAdmin":
        if not check_student_in_course(course_id, username):
            flask.flash("You are not enrolled in this course.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))

    flask.session["course_id"] = course_id

    # get the course language
    language = get_language(course_id)[0][0]

    # initialize practice prompt here based on the language of course
    practice_prompt = f"You are conversing with a student in {language}. Help them practice their language skills and do not ever switch to another language, even if they switch or ask you to. Pretend like you are having a conversation with them. Do not break character."

    # Initialize prompt usage state
    flask.session["prompt_used"] = False
    # Store the initial prompt text for future use
    flask.session["prompt_text"] = practice_prompt
    initial_response = get_gpt_response(practice_prompt)

    return flask.render_template(
        "student-practice-chat.html",
        course_id=course_id,
        initial_data=initial_response,
        prompt=practice_prompt,
        username=username,
        language=language,
        user_type=user_type,
    )

#-----------------------------------------------------------------------

@app.route("/add-course", methods=["POST"])
def add_course():
    prof_id = flask.request.form.get("course_owner")
    course_id = flask.request.form.get("course_id")
    course_name = flask.request.form.get("course_name")
    # Get the actual language text
    language = flask.request.form.get("language")

    if not course_id or not course_name:
        return flask.jsonify(
            {"message": "Course ID and name are required."}), 400

    if not any(
        prof.prof_id == prof_id for prof in get_profs()) and not any(
        admin.admin_id == prof_id for admin in get_superadmins()
    ):
        return flask.jsonify(
            {"message": "You are not allowed to create a course"}), 403

    if check_if_course_exists(course_id):
        return (
            flask.jsonify({"message": "Course with this course ID already exists."}), 400,
        )

    # Generate a random course code
    course_code = generate_course_code()
    upper_course_id = course_id.upper()
    new_course = Course(
        course_id=upper_course_id,
        course_code=course_code,
        course_name=course_name,
        owner=prof_id,
        language=language,
    )

    with sqlalchemy.orm.Session(engine) as session:
        session.add(new_course)
        session.flush()
        course_prof_link = CoursesProfs(
            course_id=new_course.course_id, prof_id=prof_id)
        session.add(course_prof_link)
        session.commit()

    return flask.jsonify({"message": "Course added successfully"})

#-----------------------------------------------------------------------

@app.route("/get-prof-courses")
def get_prof_courses():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    id = flask.session.get("username")
    course_data = get_professor_courses(id)
    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route("/get-admin-courses")
def get_admin_courses():
    username = auth.authenticate()
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for("student_dashboard"))
    course_data = get_courses_and_profs()

    if course_data is None:
        course_data = {}

    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route("/get-stu-courses")
def get_stu_courses():
    username = auth.authenticate()
    id = flask.session.get("username")
    course_data = get_student_courses(id)
    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route("/all-courses")
def all_courses():

    courses = get_courses()
    course_data = []
    for course in courses:
        course_info = {
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_code": course.course_code,
        }
        course_data.append(course_info)
    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route("/join-course", methods=["POST"])
def join_course():
    course_code = flask.request.form.get("course_code")
    student_id = flask.session.get("username")

    # Call the function from database.py
    result = enroll_student_in_course(student_id, course_code)

    if result["status"] == "error":
        return flask.jsonify({"message": result["message"]}), 400

    return flask.jsonify({"message": result["message"]})

#-----------------------------------------------------------------------

@app.route("/edit-course-code", methods=["POST"])
def update_course_code_click():
    course_id = flask.request.form.get("course_id")
    new_code = flask.request.form.get("new_course_code")

    if not new_code:
        return flask.jsonify({"message": "Invalid course code."}), 400

    try:
        if edit_course_code(course_id, new_code):
            return flask.jsonify({"message": "Course code updated successfully."})
        return (flask.jsonify({
            "message": "Code already exists for another course, choose a new code."}), 500,)
    except Exception as e:
        return flask.jsonify({"message": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/delete-course/<course_id>", methods=["POST"])
def delete_course_click(course_id):
    try:
        if delete_course(course_id):
            return flask.jsonify(
                {"message": "Course deleted successfully"}), 200

        return flask.jsonify(
            {"message": "Error Deleting course"}), 200
    except Exception as e:
        return flask.jsonify({"message": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/delete-student/<course_id>/<student_id>", methods=["POST"])
def delete_student(course_id, student_id):
    # Execute the delete operation
    if delete_student_from_course(student_id, course_id):
        return flask.jsonify(
            {"message": "Student deleted successfully"}), 200

    # If deletion was not successful, send an error response
    return flask.jsonify({"error": "Failed to delete student"}), 500

#-----------------------------------------------------------------------
@app.route("/delete-prof/<course_id>/<prof_id>", methods=["POST"])
def delete_prof(course_id, prof_id):
    if delete_prof_from_course(prof_id, course_id):
        return flask.jsonify(
            {"message": "Professor deleted successfully"}), 200

    return flask.jsonify({"error": "Failed to delete professor"}), 500

#-----------------------------------------------------------------------

@app.route("/get-assignments", methods=["GET"])
def get_assignments():
    course_id = flask.request.args.get("course_id")
    if course_id:
        try:
            assignments = get_assignments_for_course(course_id)
            return flask.jsonify(assignments)
        except Exception:
            return flask.jsonify(
                {"error": "Failed to fetch assignments"}), 500
    else:
        return flask.jsonify(
            {"error": "No course ID provided"}), 400

#-----------------------------------------------------------------------

@app.route("/add-assignment", methods=["POST"])
def add_assignment():
    assignment_name = flask.request.form.get("assignment_name")
    assignment_description = flask.request.form.get(
        "assignment_description")
    assignment_prompt = flask.request.form.get("assignment_prompt")
    num_turns = flask.request.form.get("num_turns")
    course_id = flask.request.form.get("course_id")
    deadline_str = flask.request.form.get("deadline")

    # Define Eastern Standard Time timezone
    est = pytz.timezone("America/New_York")
    utc = pytz.utc

    try:
        # Parse the deadline as EST
        local_deadline = datetime.strptime(
            deadline_str, "%Y-%m-%dT%H:%M:%S")
        # Localize the naive datetime
        local_deadline = est.localize(local_deadline)
        # Convert to UTC
        deadline = local_deadline.astimezone(utc)
    except Exception as e:
        print(f"Failed to parse deadline: {e}")
        return flask.jsonify(
            {"message": "Invalid deadline format"}), 400

    prof_id = flask.session.get("username")
    new_assignment = Prompt(
        prompt_title=assignment_name,
        course_id=course_id,
        prof_id=prof_id,
        prompt_text=assignment_prompt,
        num_turns=int(num_turns),
        deadline=deadline,
        description=assignment_description,
    )

    with sqlalchemy.orm.Session(engine) as session:
        session.add(new_assignment)
        session.commit()

    return flask.jsonify({"message": "Assignment added successfully"})

#-----------------------------------------------------------------------

@app.route("/add-professor-to-course", methods=["POST"])
def add_professor_to_course():
    course_id = flask.request.form.get("course_id")
    full_name = flask.request.form.get("prof_name")
    prof_netid = flask.request.form.get("prof_netid")
    user_type = check_user_type(prof_netid)

    if not course_id or not full_name or not prof_netid:
        return (flask.jsonify(
            {"message": "All fields (course ID, professor name, and NetID) are required."}), 400,)

    with Session() as session:
        if user_type != "SuperAdmin":
            # Check if the professor already exists by NetID
            professor = session.query(
                Professor).filter_by(prof_id=prof_netid).first()
            if not professor:
                # Splitting the name into first and last name
                name_parts = full_name.split()
                first_name = name_parts[0]
                last_name = " ".join(
                    name_parts[1:]) if len(name_parts) > 1 else ""
                professor = Professor(
                    prof_id=prof_netid,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(professor)

        # Check if the professor is already linked to the course
        existing_link = (
            session.query(CoursesProfs)
            .filter_by(course_id=course_id, prof_id=prof_netid)
            .first()
        )
        if existing_link:
            return (flask.jsonify({"message": "Professor already added to this course."}), 409,)

        # Create a new link between the professor and the course
        new_course_prof = CoursesProfs(
            course_id=course_id, prof_id=prof_netid)
        session.add(new_course_prof)
        session.commit()

    return flask.jsonify(
        {"message": "Professor added successfully to the course."})

#-----------------------------------------------------------------------

@app.route("/get-profs-in-course/<course_id>")
def get_profs_in_course(course_id):
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        profs = get_profs_for_course(course_id)
        return flask.jsonify(profs)
    except Exception:
        return flask.jsonify(
            {"error": "Failed to fetch professors"}), 500

#-----------------------------------------------------------------------
@app.route("/get-students-in-course/<course_id>")
def get_students_in_course(course_id):
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        students = get_students_for_course(course_id)
        return flask.jsonify(students)
    except Exception as e:
        print(f"Failed to fetch students: {e}")
        return flask.jsonify({"error": "Failed to fetch students"}), 500

#-----------------------------------------------------------------------

@app.route("/add-student-to-course", methods=["POST"])
def add_student_to_course():
    course_id = flask.request.form.get("course_id")
    full_name = flask.request.form.get("student_name")
    student_netid = flask.request.form.get("student_netid")

    if not course_id or not full_name or not student_netid:
        return (
            flask.jsonify(
                {"message": "All fields (course ID, student name, and NetID) are required."}), 400,)

    with Session() as session:
        # Check if the NetID belongs to a professor or superadmin
        is_professor = (
            session.query(
                Professor).filter_by(prof_id=student_netid).first()
            is not None
        )
        is_superadmin = (
            session.query(
                SuperAdmin).filter_by(admin_id=student_netid).first()
            is not None
        )

        if not is_professor and not is_superadmin:
            # Only add as a student if not a professor or superadmin
            student = session.query(
                Student).filter_by(student_id=student_netid).first()
            if not student:
                name_parts = full_name.split()
                first_name = name_parts[0]
                last_name = " ".join(
                    name_parts[1:]) if len(name_parts) > 1 else ""
                student = Student(
                    student_id=student_netid,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(student)

        # Check if the user is already linked to the course
        existing_link = (
            session.query(CoursesStudents)
            .filter_by(course_id=course_id, student_id=student_netid)
            .first()
        )
        if existing_link:
            return (flask.jsonify({"message": "Student already added to this course."}), 409,)

        # Create a new link between the user and the course
        new_course_student = CoursesStudents(
            course_id=course_id, student_id=student_netid
        )
        session.add(new_course_student)
        session.commit()

    return flask.jsonify({"message": "Student added successfully to the course."}), 200

#-----------------------------------------------------------------------

@app.route("/admin-profs")
def get_professors_and_courses():
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        data = fetch_professors_and_courses()
        return flask.jsonify(data)
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/admin-students")
def get_students_and_courses():
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        data = fetch_students_and_courses()
        return flask.jsonify(data)
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/check-enrollment/<course_id>")
def check_enrollment(course_id):
    student_id = flask.request.args.get("student_id")

    enrolled = check_student_in_course(course_id, student_id)

    return flask.jsonify({"enrolled": enrolled})

#-----------------------------------------------------------------------

@app.route("/admin-add-professor-to-course", methods=["POST"])
def admin_add_professor_to_course():
    course_id = flask.request.form.get("course_id")
    prof_name = flask.request.form.get("prof_name")
    prof_netid = flask.request.form.get("prof_netid")

    if not course_id or not prof_name or not prof_netid:
        return (flask.jsonify(
            {"message": "All fields (course ID, professor name, and NetID) are required."}), 400,)

    upper_course_id = course_id.upper()

    with Session() as session:
        # Check if the course exists
        course = session.query(
            Course).filter_by(course_id=upper_course_id).first()
        if not course:
            return flask.jsonify(
                {"message": "Course does not exist."}), 404

        # Check if the professor is a superadmin
        is_superadmin = (
            session.query(SuperAdmin).filter_by(
                admin_id=prof_netid).first() is not None
        )

        if not is_superadmin:
            # Check if the professor already exists
            professor = session.query(
                Professor).filter_by(prof_id=prof_netid).first()
            if not professor:
                # Assuming splitting name into first and last
                first_name, last_name = (
                    prof_name.split(maxsplit=1) + [""])[:2]
                professor = Professor(
                    prof_id=prof_netid,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(professor)

        # Check if the professor is already linked to the course
        existing_link = (
            session.query(CoursesProfs)
            .filter_by(course_id=upper_course_id, prof_id=prof_netid)
            .first()
        )
        if existing_link:
            return (flask.jsonify(
                {"message": "Professor already added to this course."}), 409,)

        # Create a new link between the professor and the course
        new_course_prof = CoursesProfs(
            course_id=upper_course_id, prof_id=prof_netid)
        session.add(new_course_prof)
        session.commit()

        return (flask.jsonify({"message": "Professor added successfully to the course."}), 200,)

#-----------------------------------------------------------------------

@app.route("/admin-add-student-to-course", methods=["POST"])
def admin_add_student_to_course():
    course_id = flask.request.form.get("course_id")
    student_name = flask.request.form.get("student_name")
    student_id = flask.request.form.get("student_id")

    if not course_id or not student_name or not student_id:
        return (
            flask.jsonify(
                {"message": "All fields (student ID, name, and course ID) are required."}), 400,)

    upper_course_id = course_id.upper()

    with Session() as session:
        # Check if the course exists
        course = session.query(
            Course).filter_by(course_id=upper_course_id).first()
        if not course:
            return flask.jsonify(
                {"message": "Course does not exist."}), 404

        # Check if the identifier belongs to a professor or a superadmin
        professor_or_admin = (
            session.query(
                Professor).filter_by(prof_id=student_id).first()
            or session.query(
                SuperAdmin).filter_by(admin_id=student_id).first()
        )

        if not professor_or_admin:
            # Proceed to add as a student if not professor or superadmin
            student = session.query(
                Student).filter_by(student_id=student_id).first()
            if not student:
                # Assuming splitting name into first and last
                first_name, last_name = (
                    student_name.split(maxsplit=1) + [""])[:2]
                student = Student(
                    student_id=student_id,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(student)

        # Check if the identifier (student, professor, or admin)
        # is already linked to the course
        existing_link = (
            session.query(CoursesStudents)
            .filter_by(course_id=upper_course_id, student_id=student_id)
            .first()
        )
        if existing_link:
            return (flask.jsonify({"message": "This student is already added to the course."}), 409,)

        # Link identifier (student, professor, or admin) to the course
        new_course_student = CoursesStudents(
            course_id=upper_course_id, student_id=student_id
        )
        session.add(new_course_student)
        session.commit()

        return (flask.jsonify({"message": "Student added successfully to the course."}), 200,)

#-----------------------------------------------------------------------

@app.route("/admin-admins", methods=["GET"])
def fetch_admins():
    # Call the function to get the superadmins roster
    try:
        username = auth.authenticate()
        user_type = check_user_type(username)

        if user_type == "Student":
            flask.flash("Access denied: Unauthorized access.", "error")
            return flask.redirect(flask.url_for("student_dashboard"))
        admin_list = get_superadmins_roster()
        return flask.jsonify(admin_list)
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/admin-add-admin", methods=["POST"])
def add_admin():
    admin_id = flask.request.form.get("admin_netid")
    admin_name = flask.request.form.get("admin_name")

    if admin_id is None or admin_name is None:
        return flask.jsonify(
            {"message": "Missing data for required fields"}), 400

    # Directly check if the admin already exists
    with Session() as session:
        existing_admin = (
            session.query(
                SuperAdmin.admin_id).filter_by(
                    admin_id=admin_id).first()
        )
        if existing_admin is not None:
            return flask.jsonify(
                {"message": "This user is already an admin."}), 409

        # If the admin does not exist, proceed to add them
        first_name, last_name = (
            admin_name.split(maxsplit=1) + [""])[:2]
        new_admin = SuperAdmin(
            admin_id=admin_id,
            first_name=first_name,
            last_name=last_name
        )

        session.add(new_admin)
        session.commit()

    return flask.jsonify({"message": "Admin added successfully."}), 201

#-----------------------------------------------------------------------

@app.route("/delete-admin/<adminid>", methods=["POST"])
def delete_admin(adminid):
    if not adminid:
        return flask.jsonify({"message": "Admin ID is required."}), 400

    with Session() as session:
        admin = session.query(
            SuperAdmin).filter_by(admin_id=adminid).first()
        if not admin:
            return flask.jsonify({"message": "Admin not found."}), 404

        session.delete(admin)
        session.commit()

    return flask.jsonify({"message": "Admin deleted successfully."}), 200

#-----------------------------------------------------------------------

@app.route("/score-zero", methods=["POST"])
def score_zero():
    if flask.request.method != "POST":
        return flask.jsonify({"error": "Method Not Allowed"}), 405

    try:
        data = flask.request.get_json()

        student_id = data.get("student_id")
        course_id = data.get("course_id")
        prompt_id = data.get("prompt_id")
        conversation_text = data.get("conversation_text")

        score = 0
        prof_score = None
        conv_id = generate_unique_conv_id()

        store_conversation(
            conv_id,
            course_id,
            student_id,
            prompt_id,
            conversation_text,
            score,
            prof_score,
        )

        # Clean up session
        flask.session.pop("turns_count", None)
        flask.session.pop("max_turns", None)
        flask.session.pop("conversation_text", None)

        return (flask.jsonify({"message": "Conversation recorded with a score of 0."}), 200,)
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/get-scores/<prompt_id>")
def get_scores(prompt_id):
    try:
        scores = get_all_scores(prompt_id)
        return (
            flask.jsonify(
                [
                    {
                        "student_id": score.name,
                        "score": score.score,
                        "prof_score": score.prof_score,
                        "conv_id": score.conv_id,
                    }
                    for score in scores
                ]
            ),
            200,
        )
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------

@app.route("/edit-prof-score/<int:conv_id>", methods=["POST"])
def edit_prof_score(conv_id):
    prof_score = flask.request.json.get("profScore")

    with sqlalchemy.orm.Session(engine) as session:
        conversation = session.query(
            Conversation).filter_by(conv_id=conv_id).first()
        if conversation:
            conversation.prof_score = int(prof_score)
            session.commit()
            return flask.jsonify(
                message="Score edited successfully."), 200

        return flask.jsonify(message="Conversation not found."), 404

#-----------------------------------------------------------------------

@app.route("/is-course-owner/<course_id>/<prof_id>", methods=["GET"])
def is_course_owner(course_id, prof_id):
    if check_if_owner(course_id, prof_id):
        return flask.jsonify({"isOwner": True}), 200
    return flask.jsonify({"isOwner": False}), 200

#-----------------------------------------------------------------------
