#-----------------------------------------------------------------------
# chatbot.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sys
from openai import OpenAI
import flask
import sqlalchemy
import auth
from req_lib import ReqLib
from database import (Student, Course, Conversation, CoursesStudents, engine, Base)

#-----------------------------------------------------------------------

app = flask.Flask(__name__)

Base.metadata.create_all(engine)

Session = sqlalchemy.orm.sessionmaker(bind = engine)

GPT_API_KEY = os.environ['GPT_API_KEY']
app.secret_key = '1234567'  # hardcoded

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

@app.route('/student-dashboard')
def student_dashboard():
    username = auth.authenticate()

    req_lib = ReqLib()

    req = req_lib.getJSON(
        req_lib.configs.USERS,
        uid=username
    )

    # check if req is list and extract first item
    # otherwise, handle case with no user info or wrong format
    if req and isinstance(req, list):
        user_info = req[0]  
        full_name = user_info.get("displayname", "Default User")
    else:
        full_name = "Default User"
    
    first_name = full_name.split()[0]

    return flask.render_template('student-dashboard.html', 
                                 username = username,
                                 first_name = first_name)

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

@app.route('/prof-classes')
def prof_classes():
    username = auth.authenticate()
    return flask.render_template('prof-classes.html',
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