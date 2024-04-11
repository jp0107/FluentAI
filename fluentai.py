#-----------------------------------------------------------------------
# chatbot.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import datetime
import os
import sys
import random
import string
from openai import OpenAI
import flask
import sqlalchemy
import auth
from req_lib import ReqLib
from database import (Student, Professor, SuperAdmin, Course, Conversation,
                      CoursesStudents, CoursesProfs, engine, Base, get_profs, 
                      get_superadmins, check_user_type, get_students_by_course,
                      get_student_firstname, get_prof_firstname)

#-----------------------------------------------------------------------

app = flask.Flask(__name__)

Base.metadata.create_all(engine)

Session = sqlalchemy.orm.sessionmaker(bind = engine)

GPT_API_KEY = os.environ['GPT_API_KEY']
app.secret_key = '1234567'  # hardcoded

#-----------------------------------------------------------------------
def generate_course_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))
#-----------------------------------------------------------------------

def get_gpt_response(user_input, conversation_history):
    if not GPT_API_KEY:
        print("GPT API key is missing", file=sys.stderr)
        return "Error: API key is missing."

    try:
        client = OpenAI(api_key=GPT_API_KEY)
        combined_input = conversation_history + "\nUser: " + user_input + "\nAI:"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            # response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "You are a helpful spanish teacher. \
                    Please help me practice my spanish in really basic levels."},
                {"role": "user", "content": combined_input}
            ]
        )
        response_json = response.choices[0].message.content
        return response_json

    except Exception as ex:
        print("An error occurred: ", ex, file=sys.stderr)
        return "Error: An issue occurred while processing your request."
#-----------------------------------------------------------------------

def store_conversation(student_id, course_id, prompt_id, conv_text):
    with Session() as session:
        new_conversation = Conversation(
            student_id=student_id,
            course_id=course_id,
            prompt_id=prompt_id,
            conv_text=conv_text,
        )
        session.add(new_conversation)
        session.commit()

#-----------------------------------------------------------------------

# function for storing student and prof info in the database
def store_userinfo(user_id, first_name, last_name, pustatus, email):
    with Session() as session:
        if pustatus == "undergraduate":
            new_student = Student(
                student_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            session.add(new_student)
            session.commit()
        elif pustatus == "faculty":
            new_prof = Professor(
                prof_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            session.add(new_prof)
            session.commit()

#-----------------------------------------------------------------------

# function for storing admin info in the database
def store_admininfo(user_id, first_name, last_name, email):
    with Session() as session:
        new_admin = SuperAdmin(
            admin_id=user_id,
            first_name = first_name,
            last_name = last_name,
            email = email
        )
        session.add(new_admin)
        session.commit()

#-----------------------------------------------------------------------
# Routes for authentication.

@app.route('/logoutapp', methods=['GET'])
def logoutapp():
    return auth.logoutapp()

@app.route('/logoutcas', methods=['GET'])
def logoutcas():
    return auth.logoutcas()

#-----------------------------------------------------------------------

@app.route('/')
@app.route('/index')
def home():
    return flask.render_template('index.html')

#----------------------   STUDENT PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route('/student-classes')
def student_classes():
    username = auth.authenticate()

    # if new user, store user info in database
    user_type = check_user_type(username)

    if user_type is None:
        req_lib = ReqLib()

        req = req_lib.getJSON(
            req_lib.configs.USERS,
            uid=username
        )

        # get user first/last name, email, and pustatus from netid
        user_info = req[0]  

        full_name = user_info.get("displayname")
        temp = full_name.split()
        first_name = temp[0]
        last_name = temp[-1]

        pustatus = user_info.get("pustatus")
        email = user_info.get("mail")

        # store user info in corresponding table
        store_userinfo(username, first_name, last_name, pustatus, email)
    
    # direct user to the correct page based on user type
    # if user_type == "Student":
    #     # Fetch student-specific data and render the student dashboard
    #     pass

    # elif user_type == "Professor":
    #     return flask.redirect('/prof-classes')
    # else:
    #     return flask.redirect('/admin-classes')

    html_code = flask.render_template(
        'student-classes.html', username = username)
    return flask.make_response(html_code)

#-----------------------------------------------------------------------

@app.route('/student-all-classes')
def student_all_classes():
    username = auth.authenticate()

    html_code = flask.render_template(
        'student-all-classes.html', username = username)
    return flask.make_response(html_code)

#-----------------------------------------------------------------------

@app.route('/student-prototype')
def student_classes_2():
    username = auth.authenticate()
    html_code = flask.render_template(
        'student-prototype.html', username = username)
    return flask.make_response(html_code)

#-----------------------------------------------------------------------

@app.route('/student-dashboard')
def student_dashboard():
    username = auth.authenticate()
    
    # get user's first name to display on dashboard
    first_name = get_student_firstname(username)

    return flask.render_template('student-dashboard.html', 
                                 username = username,
                                 first_name = first_name,
                                )

#-----------------------------------------------------------------------

@app.route('/student-assignments')
def student_assignments():
    username = auth.authenticate()
    return flask.render_template('student-assignments.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/student-practice')
def student_practice():
    username = auth.authenticate()
    return flask.render_template('student-practice.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/student-scores')
def student_scores():
    username = auth.authenticate()
    return flask.render_template('student-scores.html',
                                 username = username)

#------------------------  PROFESSOR PAGES   ---------------------------
#-----------------------------------------------------------------------

@app.route('/prof-classes')
def prof_classes():
    username = auth.authenticate()
    return flask.render_template('prof-classes.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/prof-dashboard')
def prof_dashboard():
    username = auth.authenticate()

    # get user's first name to display on dashboard
    first_name = get_prof_firstname(username)

    return flask.render_template('prof-dashboard.html',
                                 username = username,
                                 first_name = first_name)

#-----------------------------------------------------------------------

@app.route('/prof-assignments')
def prof_assignments():
    username = auth.authenticate()
    return flask.render_template('prof-assignments.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/prof-roster')
def prof_roster():
    username = auth.authenticate()
    hardcoded_courseid = "cos333"  # Hardcoded value

    roster = get_students_by_course(hardcoded_courseid)

    return flask.render_template('prof-roster.html',
                                 username = username,
                                 course_id = hardcoded_courseid,
                                 students = roster
                                 )

#-----------------------------------------------------------------------

@app.route('/prof-scores')
def prof_scores():
    username = auth.authenticate()

    return flask.render_template('prof-scores.html',
                                 username = username,
                                 )
                                
#----------------------      ADMIN PAGES    ----------------------------
#-----------------------------------------------------------------------

@app.route('/admin-dashboard')
def admin_dashboard():
    username = auth.authenticate()
    return flask.render_template('admin-dashboard.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/admin-courses')
def admin_courses():
    username = auth.authenticate()
    return flask.render_template('admin-courses.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/admin-prof-roster')
def admin_prof_roster():
    username = auth.authenticate()
    return flask.render_template('admin-prof-roster.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/admin-student-roster')
def admin_student_roster():
    username = auth.authenticate()
    return flask.render_template('admin-student-roster.html',
                                 username = username)

#------------------------   OTHER PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route('/conversation-history')
def conversation_history():
    username = auth.authenticate()
    return flask.render_template('conversation-history.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/assignment-chat')
def assignment_chat():
    username = auth.authenticate()
    return flask.render_template('assignment-chat.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/practice-chat')
def practice_chat():
    username = auth.authenticate()
    return flask.render_template('practice-chat.html',
                                 username = username)

#-----------------------------------------------------------------------
@app.route('/fetch-conversation')
def fetch_conversation():
    username = auth.authenticate()
    hardcoded_student_id = 123  # Hardcoded value

    with Session() as session:
        conversations = session.query(Conversation).filter(
            Conversation.student_id == hardcoded_student_id).all()
        conversation_texts = [conv.conv_text for conv in conversations]
        return flask.render_template(
            'assignment-chat.html', 
            username = username,
            conversation_data=conversation_texts)

#-----------------------------------------------------------------------
@app.route('/process-gpt-request', methods=['POST'])
def process_gpt_request():
    username = auth.authenticate()

    user_input = flask.request.form['userInput']

    # Retrieve the GPT response (modify as needed)
    gpt_response = get_gpt_response(user_input, " ")

    store_conversation(
        123, 456, 789, "User: " + user_input + "\nAI: " + gpt_response)

    # Render index.html again with the GPT response
    return flask.render_template(
        'assignment-chat.html', 
        username = username,
        data=gpt_response)
#-----------------------------------------------------------------------

@app.route('/add-course', methods=['POST'])
def add_course():
    course_id = flask.request.form.get('course_id')
    course_name = flask.request.form.get('course_name')
    course_description = flask.request.form.get('course_description')
    language = flask.request.form.get('language')  # Get the actual language text

    if not course_id or not course_name:
        return flask.jsonify({"message": "Course ID and name are required."}), 400

    prof_id = flask.session.get('username')  # Assuming this is set correctly in the session

    if not any(prof.prof_id == prof_id for prof in get_profs()) and \
       not any(admin.admin_id == prof_id for admin in get_superadmins()):
        return flask.jsonify({"message": "You are not allowed to create a course"}), 403

    course_code = generate_course_code()  # Generate a random course code
    new_course = Course(course_id=course_id, course_code=course_code, course_name=course_name, course_description=course_description, owner=prof_id, language=language)

    with sqlalchemy.orm.Session(engine) as session:
        session.add(new_course)
        session.flush()
        course_prof_link = CoursesProfs(course_id=new_course.course_id, prof_id=prof_id)
        session.add(course_prof_link)
        session.commit()

    return flask.jsonify({"message": "Course added successfully"})

#-----------------------------------------------------------------------

@app.route('/get-courses', methods=['GET'])
def get_courses():
    # Fetch courses from the database
    courses = ...  # Retrieve courses from the database
    return flask.jsonify(courses)

#-----------------------------------------------------------------------

