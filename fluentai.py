#-----------------------------------------------------------------------
# fluentai.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sys
import random
import datetime
import string
from openai import OpenAI, APIError
import flask
import sqlalchemy
import auth
from req_lib import ReqLib
from database import (Student, Professor, SuperAdmin, Course, Conversation,
                      CoursesStudents, CoursesProfs, engine, Base, Prompt, get_profs, get_all_profs,
                      get_superadmins, check_user_type, get_student_firstname, get_professor_courses,
                      get_prof_firstname, get_courses, get_student_courses, enroll_student_in_course, get_course_code,
                      edit_course_code, get_admin_firstname, get_prompt_by_id, get_practice_prompts, get_default_practice,
                      get_assignments_and_scores_for_student, get_default_student_scores, get_conversation, get_default_conversation, get_courses_and_profs, get_prof_info, get_student_info,
                      get_profs_for_course, get_assignments_for_course, get_assignments_for_student,
                      get_prompt_title, get_students_for_course, get_language, fetch_professors_and_courses)

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
        if (pustatus in ("undergraduate", "graduate")):
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
def delete_course(course_id):
    with Session() as session:
        try:
            # Delete associated professor entries, if any
            profs_deleted = session.query(CoursesProfs).filter(CoursesProfs.course_id == course_id).delete()
            print(f"Deleted {profs_deleted} professor associations for course ID {course_id}")

            # Delete associated student entries, if any
            students_deleted = session.query(CoursesStudents).filter(CoursesStudents.course_id == course_id).delete()
            print(f"Deleted {students_deleted} student associations for course ID {course_id}")

            # Try to find and delete the course itself
            course_entry_to_delete = session.query(Course).filter(Course.course_id == course_id).one_or_none()
            if course_entry_to_delete:
                session.delete(course_entry_to_delete)
                session.commit()
                print("Course deleted successfully.")
                return True
            
            # No course found to delete; not necessarily an error, but nothing was done
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
            conversations_deleted = session.query(Conversation).filter(Conversation.prompt_id == prompt_id).delete()
            print(f"Deleted {conversations_deleted} conversations for prompt ID {prompt_id}")

            # Now try to find and delete the assignment itself
            prompt_entry_to_delete = session.query(Prompt).filter(Prompt.prompt_id == prompt_id).one_or_none()
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
            # Delete the association between the professor and the course
            association_deleted = session.query(CoursesProfs).filter(
                CoursesProfs.prof_id == prof_id,
                CoursesProfs.course_id == course_id
            ).delete(synchronize_session=False)

            if association_deleted:
                session.commit()
                print(f"Deleted association for professor ID {prof_id} from course ID {course_id}")
                return True
            
            print("No association found to delete.")
            return False
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return False

#-----------------------------------------------------------------------        

def delete_student_from_course(student_id, course_id):
    with Session() as session:
        try:
            # Delete the association between the student and the course
            association_deleted = session.query(CoursesStudents).filter(
                CoursesStudents.student_id == student_id,
                CoursesStudents.course_id == course_id
            ).delete(synchronize_session=False)

            if association_deleted:
                session.commit()
                print(f"Deleted association for student ID {student_id} from course ID {course_id}")
                return True
            
            print("No association found to delete.")
            return False
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return False

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

#-----------------------------------------------------------------------
@app.route('/login')
def login():
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

    user_type = check_user_type(username)

    if user_type == "Student":
        return flask.redirect(flask.url_for('student_classes'))
    if user_type == "Professor":
        return flask.redirect(flask.url_for('prof_classes'))
    if user_type == "SuperAdmin":
        return flask.redirect(flask.url_for('admin_dashboard'))

    return "Login Required", 401

#----------------------   STUDENT PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route('/student-classes')
def student_classes():
    username = auth.authenticate()

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
    user_type = check_user_type(username)
    if(user_type == "Student"):
        first_name = get_student_firstname(username)
    elif(user_type == "Professor"):
        first_name = get_prof_firstname(username)
    elif(user_type == "SuperAdmin"):
        first_name = get_admin_firstname(username)

    return flask.render_template('student-dashboard.html', 
                                 username = username,
                                 first_name = first_name,
                                 course_id = course_id
                                )

#-----------------------------------------------------------------------

@app.route('/student-assignments/<course_id>')
def student_assignments(course_id):
    username = auth.authenticate()  # Assuming this retrieves the student ID

    flask.session['course_id'] = course_id
    try:
        curr_assignments, past_assignments = get_assignments_for_student(username, course_id)
    except Exception:
        return flask.jsonify({'error': 'Failed to fetch assignments'}), 500
    return flask.render_template('student-assignments.html',
                                 username=username,
                                 course_id=course_id,
                                 curr_assignments=curr_assignments,
                                 past_assignments=past_assignments
                                 )

#-----------------------------------------------------------------------

@app.route('/student-practice/<course_id>')
def student_practice(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    try:
        practice_assignments = get_practice_prompts(course_id)
    except:
        practice_assignments = get_default_practice()

    return flask.render_template('student-practice.html',
                                 username = username,
                                 course_id = course_id,
                                 practice_assignments = practice_assignments)

#-----------------------------------------------------------------------

@app.route('/student-scores/<course_id>')
def student_scores(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    scores = get_assignments_and_scores_for_student(course_id, username)

    return flask.render_template('student-scores.html',
                                 username = username,
                                 course_id = course_id,
                                 scores = scores)

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
    # get user's type to make sure they can access page and display name if correct
    user_type = check_user_type(username)

    if user_type == "Student":
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for('student_classes'))  # Redirecting to the home page or a suitable route
    if(user_type == "Professor"):
        first_name = get_prof_firstname(username)
    elif(user_type == "SuperAdmin"):
        first_name = get_admin_firstname(username)


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
@app.route('/delete-assignment/<int:prompt_id>', methods=['POST'])
def delete_assignment_click(prompt_id):
    try:
        if delete_assignment(prompt_id):
            return flask.jsonify({'message': 'Assignment deleted successfully'}), 200
        
        return flask.jsonify({'message': 'Error deleting assignment'}), 200
    except Exception as e:
        return flask.jsonify({'message': str(e)}), 500

#-----------------------------------------------------------------------



@app.route('/prof-roster/<course_id>')
def prof_roster(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    return flask.render_template('prof-roster.html',
                                 username = username,
                                 course_id = course_id)

#-----------------------------------------------------------------------

@app.route('/prof-scores/<course_id>')
def prof_scores(course_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    try:
        scores = get_assignments_and_scores_for_student(course_id, username)
    except:
        scores = get_default_student_scores()

    return flask.render_template('prof-scores.html',
                                 username = username,
                                 course_id = course_id,
                                 scores = scores
                                 )
                                
#----------------------      ADMIN PAGES    ----------------------------
#-----------------------------------------------------------------------

@app.route('/admin-dashboard')
def admin_dashboard():
    username = auth.authenticate()

    # get user's type to make sure they can access page and display name if correct
    user_type = check_user_type(username)
    
    if (user_type == "Student"):
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for('student_classes'))  # Redirecting to the home page or a suitable route
    if(user_type == "Professor"):
        flask.flash("Access denied: Unauthorized access.", "error")
        return flask.redirect(flask.url_for('prof_classes'))  # Redirecting to the home page or a suitable route
    if(user_type == "SuperAdmin"):
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

    prof_list = get_prof_info()

    return flask.render_template('admin-prof-roster.html',
                                 username = username,
                                 prof_list = prof_list)

#-----------------------------------------------------------------------

@app.route('/admin-student-roster')
def admin_student_roster():
    username = auth.authenticate()

    student_list = get_student_info()

    return flask.render_template('admin-student-roster.html',
                                 username = username,
                                 student_list = student_list)

#------------------------   OTHER PAGES   ------------------------------
#-----------------------------------------------------------------------

@app.route('/conversation-history/<course_id>/<int:conv_id>')
def conversation_history(course_id, conv_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    try:
        conversation = get_conversation(course_id, username, conv_id)
    except:
        conversation = get_default_conversation()

    return flask.render_template('conversation-history.html',
                                 username = username,
                                 course_id = course_id,
                                 conversation = conversation)

#-----------------------------------------------------------------------

@app.route('/student-assignment-chat/<course_id>/<int:prompt_id>')
def student_assignment_chat(course_id, prompt_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    # Use the function from database.py to fetch the prompt
    prompt = get_prompt_by_id(prompt_id)

    # get the course language
    language = get_language(course_id)[0][0]

    if not prompt:
        # Handle cases where no prompt is found for the given ID
        return "Prompt not found", 404
    
    # get prompt title
    title = get_prompt_title(prompt_id)[0][0]
    
    flask.session['prompt_used'] = False  # Initialize prompt usage state
    flask.session['prompt_text'] = prompt.prompt_text  # Store the initial prompt text for future use
    initial_response = get_gpt_response(prompt.prompt_text)
    # Render the chat page with the initial prompt data
    return flask.render_template('student-assignment-chat.html',
                                course_id = course_id,
                                prompt_title = title,
                                initial_data=initial_response,
                                prompt=prompt.prompt_text,
                                username=username,
                                language = language)

#-----------------------------------------------------------------------

@app.route('/prof-assignment-chat/<course_id>/<int:prompt_id>')
def prof_assignment_chat(course_id, prompt_id):
    username = auth.authenticate()

    flask.session['course_id'] = course_id

    # get the course language
    language = get_language(course_id)[0][0]

    # Use the function from database.py to fetch the prompt
    prompt = get_prompt_by_id(prompt_id)
    if not prompt:
        # Handle cases where no prompt is found for the given ID
        return "Prompt not found", 404
    
    # get prompt title
    title = get_prompt_title(prompt_id)[0][0]
    
    flask.session['prompt_used'] = False  # Initialize prompt usage state
    flask.session['prompt_text'] = prompt.prompt_text  # Store the initial prompt text for future use
    initial_response = get_gpt_response(prompt.prompt_text)
    # Render the chat page with the initial prompt data
    return flask.render_template('prof-assignment-chat.html',
                                course_id = course_id,
                                prompt_title = title,
                                initial_data=initial_response,
                                prompt=prompt.prompt_text,
                                username=username,
                                language = language)

#-----------------------------------------------------------------------

@app.route('/process-input', methods=['POST'])
def process_input():
    user_input = flask.request.form.get('userInput', '')
    if not user_input:
        return flask.jsonify({'error': 'No input provided'}), 400

    if not flask.session.get('prompt_used', False):
        prompt_text = flask.session.get('prompt_text', '')  # Use the stored prompt text
        flask.session['prompt_used'] = True  # Mark the prompt as used
    else:
        prompt_text = ""

    response_text = get_gpt_response(prompt_text, user_input)
    return flask.jsonify({'gpt_response': response_text})

#-----------------------------------------------------------------------

@app.route('/student-practice-chat/<course_id>')
def student_practice_chat(course_id):
    username = auth.authenticate()
    flask.session['course_id'] = course_id

    # get the course language
    language = get_language(course_id)[0][0]

    # initialize practice prompt here based on the language of the course
    practice_prompt = f"You are conversing with a student in {language}. Help them practice their language skills and do not ever switch to another language, even if they switch or ask you to. Pretend like you are having a conversation with them."

    flask.session['prompt_used'] = False  # Initialize prompt usage state
    flask.session['prompt_text'] = practice_prompt  # Store the initial prompt text for future use
    initial_response = get_gpt_response(practice_prompt)

    return flask.render_template('student-practice-chat.html',
                                 course_id = course_id,
                                 initial_data = initial_response,
                                 prompt = practice_prompt,
                                 username = username,
                                 language = language)

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
    prof_id = flask.request.form.get('course_owner')
    course_id = flask.request.form.get('course_id')
    course_name = flask.request.form.get('course_name')
    language = flask.request.form.get('language')  # Get the actual language text

    if not course_id or not course_name:
        return flask.jsonify({"message": "Course ID and name are required."}), 400

    if not any(prof.prof_id == prof_id for prof in get_profs()) and \
       not any(admin.admin_id == prof_id for admin in get_superadmins()):
        return flask.jsonify({"message": "You are not allowed to create a course"}), 403

    course_code = generate_course_code()  # Generate a random course code
    new_course = Course(course_id=course_id, course_code=course_code, course_name=course_name, owner=prof_id, language=language)

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

@app.route('/get-admin-courses')
def get_admin_courses():
    course_data = get_courses_and_profs()

    if course_data is None:
        course_data = {}
        
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

@app.route('/delete-course/<course_id>', methods=['POST'])
def delete_course_click(course_id):
    try:
        if delete_course(course_id):
            return flask.jsonify({'message': 'Course deleted successfully'}), 200
        
        return flask.jsonify({'message': 'Error Deleting course'}), 200
    except Exception as e:
        return flask.jsonify({'message': str(e)}), 500

#-----------------------------------------------------------------------

@app.route('/delete-student/<course_id>/<student_id>', methods=['POST'])
def delete_student(course_id, student_id):
    # Execute the delete operation
    if delete_student_from_course(student_id, course_id):
        return flask.jsonify({'message': 'Student deleted successfully'}), 200
    
    # If deletion was not successful, send an error response
    return flask.jsonify({'error': 'Failed to delete student'}), 500

#-----------------------------------------------------------------------
@app.route('/delete-prof/<course_id>/<prof_id>', methods=['POST'])
def delete_prof(course_id, prof_id):
    if delete_prof_from_course(prof_id, course_id):
        return flask.jsonify({'message': 'Professor deleted successfully'}), 200
    
    return flask.jsonify({'error': 'Failed to delete professor'}), 500

#-----------------------------------------------------------------------
@app.route('/get-assignments', methods=['GET'])
def get_assignments():
    course_id = flask.request.args.get('course_id')
    if course_id:
        try:
            assignments = get_assignments_for_course(course_id)
            return flask.jsonify(assignments)
        except Exception:
            return flask.jsonify({'error': 'Failed to fetch assignments'}), 500
    else:
        return flask.jsonify({'error': 'No course ID provided'}), 400

#-----------------------------------------------------------------------
@app.route('/add-assignment', methods=['POST'])
def add_assignment():
    assignment_name = flask.request.form.get('assignment_name')
    assignment_description = flask.request.form.get('assignment_description')
    assignment_prompt = flask.request.form.get('assignment_prompt')
    num_turns = flask.request.form.get('num_turns')
    course_id = flask.request.form.get('course_id')
    deadline_str = flask.request.form.get('deadline')
    
    if deadline_str:
        try:
            deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return flask.jsonify({"message": "Invalid deadline format"}), 400
    else:
        deadline = None


    if not all([assignment_name, assignment_description, assignment_prompt, num_turns, course_id]):
        return flask.jsonify({"message": "All fields are required."}), 400


    prof_id = flask.session.get('username')
    new_assignment = Prompt(
        prompt_title=assignment_name,
        course_id=course_id,
        prof_id=prof_id,
        prompt_text=assignment_prompt,
        num_turns=int(num_turns),
        deadline=deadline,  
        assignment_description = assignment_description
    )

    with sqlalchemy.orm.Session(engine) as session:
        session.add(new_assignment)
        session.commit()

    return flask.jsonify({"message": "Assignment added successfully"})
#-----------------------------------------------------------------------

@app.route('/add-professor-to-course', methods=['POST'])
def add_professor_to_course():
    course_id = flask.request.form.get('course_id')
    full_name = flask.request.form.get('prof_name')
    prof_netid = flask.request.form.get('prof_netid')
    user_type = check_user_type(prof_netid)

    if not course_id or not full_name or not prof_netid:
        return flask.jsonify({"message": "All fields (course ID, professor name, and NetID) are required."}), 400

    with Session() as session:
        if user_type != "SuperAdmin":
            # Check if the professor already exists by NetID
            professor = session.query(Professor).filter_by(prof_id=prof_netid).first()
            if not professor:
                # Splitting the name into first and last name
                name_parts = full_name.split()
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                professor = Professor(prof_id=prof_netid, first_name=first_name, last_name=last_name)
                session.add(professor)

        # Check if the professor is already linked to the course
        existing_link = session.query(CoursesProfs).filter_by(course_id=course_id, prof_id=prof_netid).first()
        if existing_link:
            return flask.jsonify({"message": "Professor already added to this course."}), 409

        # Create a new link between the professor and the course
        new_course_prof = CoursesProfs(course_id=course_id, prof_id=prof_netid)
        session.add(new_course_prof)
        session.commit()

    return flask.jsonify({"message": "Professor added successfully to the course."})
#-----------------------------------------------------------------------
@app.route('/get-profs-in-course/<course_id>')
def get_profs_in_course(course_id):
    try:
        profs = get_profs_for_course(course_id)
        return flask.jsonify(profs)
    except Exception:
        return flask.jsonify({'error': 'Failed to fetch professors'}), 500
#-----------------------------------------------------------------------
@app.route('/get-students-in-course/<course_id>')
def get_students_in_course(course_id):
    try:
        students = get_students_for_course(course_id)
        return flask.jsonify(students)
    except Exception as e:
        print(f"Failed to fetch students: {e}")
        return flask.jsonify({'error': 'Failed to fetch students'}), 500
#-----------------------------------------------------------------------
@app.route('/add-student-to-course', methods=['POST'])
def add_student_to_course():
    course_id = flask.request.form.get('course_id')
    full_name = flask.request.form.get('student_name')
    student_netid = flask.request.form.get('student_netid')

    if not course_id or not full_name or not student_netid:
        return flask.jsonify({"message": "All fields (course ID, student name, and NetID) are required."}), 400

    with Session() as session:
        # Check if the student already exists by NetID
        student = session.query(Student).filter_by(student_id=student_netid).first()
        if not student:
            # Splitting the name into first and last name
            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            student = Student(student_id=student_netid, first_name=first_name, last_name=last_name)
            session.add(student)

        # Check if the student is already linked to the course
        existing_link = session.query(CoursesStudents).filter_by(course_id=course_id, student_id=student_netid).first()
        if existing_link:
            return flask.jsonify({"message": "Student already added to this course."}), 409

        # Create a new link between the student and the course
        new_course_student = CoursesStudents(course_id=course_id, student_id=student_netid)
        session.add(new_course_student)
        session.commit()

    return flask.jsonify({"message": "Student added successfully to the course."})
#-----------------------------------------------------------------------
@app.route('/admin-profs')
def get_professors_and_courses():
    try:
        data = fetch_professors_and_courses()
        return flask.jsonify(data)
    except Exception as e:
        return flask.sonify({'error': str(e)}), 500
#-----------------------------------------------------------------------

@app.route('/check-enrollment/<course_id>')
def check_enrollment(course_id):
    student_id = flask.session.get('student_id')  # Assuming the student's ID is stored in the session

    with sqlalchemy.orm.Session(engine) as session:
        enrollment = session.query(CoursesStudents).filter_by(
            course_id=course_id,
            student_id=student_id
        ).first()
        return flask.jsonify({"enrolled": bool(enrollment)})
