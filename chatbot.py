#-----------------------------------------------------------------------
# reg.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import sys
import os
import openai
import flask
import sqlalchemy
from database import *

#-----------------------------------------------------------------------

app = flask.Flask(__name__)

Session = sqlalchemy.orm.sessionmaker(bind = engine)

client = openai.OpenAI()


#-----------------------------------------------------------------------

gpt_api_key = os.getenv('GPT_API_KEY')

def get_gpt_response(user_input, conversation_history):
    if not gpt_api_key:
        print("GPT API key is missing", file=sys.stderr)
        return "Error: API key is missing."

    try:
        openai.api_key = gpt_api_key
        combined_input = conversation_history + "\nUser: " + user_input + "\nAI:"
        response = client.chat.completions.create(
            engine="gpt-3.5-turbo-0125",
            prompt="placeholder",
            max_tokens=200
        )
        return response.choices[0].text.strip()

    except Exception as ex:
        print("An error occurred: ", ex, file=sys.stderr)
        return "Error: An issue occurred while processing your request."

#-----------------------------------------------------------------------

@app.route('/student/<int:student_id>', methods=['GET'])
def get_student_info(student_id):
    with Session() as session:
        # Fetch student's basic info
        student = session.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            return flask.jsonify({"error": "Student not found"}), 404

        student_info = {
            "id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "created_at": student.created_at
        }

        # Fetch courses enrolled by the student
        courses = session.query(CoursesStudents, Course).join(
            Course, CoursesStudents.course_id == Course.course_id
        ).filter(CoursesStudents.student_id == student_id).all()

        student_info["courses"] = [{
            "course_id": course.Course.course_id,
            "course_name": course.Course.course_name,
            "course_description": course.Course.course_description
        } for course in courses]

        # Fetch conversation history
        conversations = session.query(Conversation).filter(
            Conversation.student_id == student_id
        ).order_by(Conversation.created_at).all()

        student_info["conversations"] = [{
            "conv_id": conv.conv_id,
            "prompt_id": conv.prompt_id,
            "text": conv.conv_text,
            "created_at": conv.created_at
        } for conv in conversations]

        return flask.jsonify(student_info)

#-----------------------------------------------------------------------
@app.route('/ask', methods=['POST'])
@app.route('/ask', methods=['POST'])
def ask():
    data = flask.request.json
    user_input = data['input']
    course_id = data.get('course_id')  
    student_id = data.get('student_id')
    prompt_id = data.get('prompt_id')

    # Retrieve the conversation history from the database
    with Session() as session:
        conversation_history = session.query(Conversation).filter(
            Conversation.course_id == course_id,
            Conversation.student_id == student_id,
            Conversation.prompt_id == prompt_id
        ).order_by(Conversation.created_at).all()
        
        # Concatenate the conversation history
        history_text = "\n".join([conv.conv_text for conv in conversation_history])

        # Get the GPT response with the conversation history
        response = get_gpt_response(user_input, history_text)

        # Create a new conversation entry
        new_conversation = Conversation(
            course_id=course_id,
            student_id=student_id,
            prompt_id=prompt_id,
            conv_text="User: " + user_input + "\nAI: " + response,
            score=0,  # Placeholder for score
            created_at=sqlalchemy.func.now
        )
        session.add(new_conversation)
        session.commit()

    return flask.jsonify({"response": response})
