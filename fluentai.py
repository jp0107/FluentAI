#-----------------------------------------------------------------------
# chatbot.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sys
import random
import string
from openai import OpenAI
import flask
import logging
import sqlalchemy
import auth
from req_lib import ReqLib
from database import (Student, Professor, SuperAdmin, Course, Conversation,
                      CoursesStudents, CoursesProfs, engine, Base, get_profs, get_all_profs,
                      get_superadmins, check_user_type, get_students_by_course, get_student_firstname, get_professor_courses,
                      get_prof_firstname, get_courses, get_student_courses, enroll_student_in_course, get_course_code,
                      edit_course_code, get_admin_firstname, delete_course, get_prompt_by_id, get_current_assignments_for_student,
                      get_score_for_student, get_past_assignments)

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

def get_gpt_response(prompt_text, user_input=""):
    if not GPT_API_KEY:
        print("GPT API key is missing", file=sys.stderr)
        return "Error: API key is missing."

    try:
        client = OpenAI(api_key=GPT_API_KEY)
        # combined_input = conversation_history + "\nUser: " + user_input + "\nAI:"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            # response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content

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

@app.route('/student-dashboard/<course_id>')
def student_dashboard(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id
    
    # get user's first name to display on dashboard
    first_name = get_student_firstname(username)

    return flask.render_template('student-dashboard.html', 
                                 username = username,
                                 first_name = first_name,
                                 course_id = course_id
                                )

#-----------------------------------------------------------------------

@app.route('/student-assignments/<course_id>')
def student_assignments(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    try:
        curr_assignments = get_current_assignments_for_student(username, course_id)
        past_assignments = get_past_assignments(course_id)
    except Exception as e:
        logging.error("Error fetching assignments for course %s: %s", course_id, str(e))
        flask.flash("An error occurred while fetching assignments. Please try again later.", "error")
        # Handle empty assignments in case of error
        curr_assignments, past_assignments = [], []

    return flask.render_template('student-assignments.html',
                                 username = username,
                                 course_id = course_id,
                                 curr_assignments = curr_assignments,
                                 past_assignments = past_assignments
                                 )

#-----------------------------------------------------------------------

@app.route('/student-practice/<course_id>')
def student_practice(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    return flask.render_template('student-practice.html',
                                 username = username,
                                 course_id = course_id)

#-----------------------------------------------------------------------

@app.route('/student-scores/<course_id>')
def student_scores(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    return flask.render_template('student-scores.html',
                                 username = username,
                                 course_id = course_id)

#------------------------  PROFESSOR PAGES   ---------------------------
#-----------------------------------------------------------------------

@app.route('/prof-classes')
def prof_classes():
    username = auth.authenticate()
    return flask.render_template('prof-classes.html',
                                 username = username)

#-----------------------------------------------------------------------

@app.route('/prof-dashboard/<course_id>')
def prof_dashboard(course_id):
    username = auth.authenticate()

    # get user's first name to display on dashboard
    first_name = get_prof_firstname(username)

    flask.session['course_id'] = course_id

    # get course code for this course
    course_code = get_course_code(course_id)[0][0]

    return flask.render_template('prof-dashboard.html',
                                 username = username,
                                 first_name = first_name,
                                 course_id = course_id,
                                 course_code = course_code)

#-----------------------------------------------------------------------

@app.route('/prof-assignments/<course_id>')
def prof_assignments(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    return flask.render_template('prof-assignments.html',
                                 username = username,
                                 course_id = course_id)

#-----------------------------------------------------------------------

@app.route('/prof-roster/<course_id>')
def prof_roster(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    roster = get_students_by_course(course_id)

    full_names = [f"{first} {last}" for student_id, first, last in roster]

    return flask.render_template('prof-roster.html',
                                 username = username,
                                 course_id = course_id,
                                 students = full_names
                                 )

#-----------------------------------------------------------------------

@app.route('/prof-scores/<course_id>')
def prof_scores(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    return flask.render_template('prof-scores.html',
                                 username = username,
                                 course_id = course_id
                                 )
                                
#----------------------      ADMIN PAGES    ----------------------------
#-----------------------------------------------------------------------

@app.route('/admin-dashboard')
def admin_dashboard():
    username = auth.authenticate()

    # get user's first name to display on dashboard
    first_name = get_admin_firstname(username)

    return flask.render_template('admin-dashboard.html',
                                 username = username,
                                 first_name = first_name)

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
    prof_list = get_all_profs()
    return flask.render_template('admin-prof-roster.html',
                                 prof_list = prof_list,
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

@app.route('/assignment-chat/<int:prompt_id>')
def assignment_chat(prompt_id):
    username = auth.authenticate()

    # Use the function from database.py to fetch the prompt
    prompt = get_prompt_by_id(prompt_id)
    if not prompt:
        # Handle cases where no prompt is found for the given ID
        return "Prompt not found", 404
    
    session['prompt_used'] = False  # Initialize prompt usage state
    initial_response = get_gpt_response(prompt.prompt_text)
    # Render the chat page with the initial prompt data
    return flask.render_template('assignment-chat.html',  initial_data=initial_response, prompt=prompt.prompt_text, username=username)

#-----------------------------------------------------------------------

@app.route('/process-input', methods=['POST'])
def process_input():
    user_input = flask.request.form.get('userInput', '')
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    if not session.get('prompt_used', False):
        prompt_text = get_prompt_by_id(some_id).prompt_text  # Fetch the prompt text only the first time
        session['prompt_used'] = True
    else:
        prompt_text = ""

    response_text = get_gpt_response(prompt_text, user_input)
    return jsonify({'gpt_response': response_text})

#-----------------------------------------------------------------------


@app.route('/practice-chat')
def practice_chat():
    username = auth.authenticate()
    return flask.render_template('practice-chat.html',
                                 username = username)

#-----------------------------------------------------------------------
# @app.route('/fetch-conversation')
# def fetch_conversation():
#     username = auth.authenticate()
#     hardcoded_student_id = 123  # Hardcoded value

#     with Session() as session:
#         conversations = session.query(Conversation).filter(
#             Conversation.student_id == hardcoded_student_id).all()
#         conversation_texts = [conv.conv_text for conv in conversations]
#         return flask.render_template(
#             'assignment-chat.html', 
#             username = username,
#             conversation_data=conversation_texts)

#-----------------------------------------------------------------------

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

@app.route('/get-prof-courses')
def get_prof_courses():
    id = flask.session.get('username') 
    course_data = get_professor_courses(id)
    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route('/get-stu-courses')
def get_stu_courses():
    id = flask.session.get('username') 
    course_data = get_student_courses(id)
    return flask.jsonify(course_data)

#-----------------------------------------------------------------------

@app.route('/all-courses')
def all_courses():
    courses = get_courses()  # Assuming get_courses() fetches all courses
    course_data = []
    for course in courses:
        course_info = {
            "course_id": course.course_id,
            "course_name": course.course_name
        }
        course_data.append(course_info)
    return flask.jsonify(course_data)


#-----------------------------------------------------------------------

@app.route('/join-course', methods=['POST'])
def join_course():
    course_code = flask.request.form.get('course_code')
    student_id = flask.session.get('username')  # Assuming student's username is in the session

    # Call the function from database.py
    result = enroll_student_in_course(student_id, course_code)

    if result["status"] == "error":
        return flask.jsonify({"message": result["message"]}), 400

    return flask.jsonify({"message": result["message"]})


#-----------------------------------------------------------------------

@app.route('/edit-course-code', methods=['POST'])
def update_course_code_click():
    course_id = flask.request.form.get('course_id')
    new_code = flask.request.form.get('new_course_code')

    if not new_code:
        return flask.jsonify({'message': 'Invalid course code!'}), 400
    
    try:
        if edit_course_code(course_id, new_code):  
            return flask.jsonify({'message': 'Course code updated successfully!'})
        else:
            return flask.jsonify({'message': 'Update failed!'}), 500
    except Exception as e:
        return flask.jsonify({'message': str(e)}), 500

#-----------------------------------------------------------------------

@app.route('/delete-course', methods=['POST'])
def delete_course_click():
    course_id = flask.request.form.get('course_id')

    try:
        if delete_course(course_id):
            return flask.jsonify({'message': 'Course deleted successfully'}), 200
        else:
            return flask.jsonify({'message': 'Error deleting course'}), 200
    except Exception as e:
        return flask.jsonify({'message': str(e)}), 500
