#-----------------------------------------------------------------------
# database.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sqlalchemy
import sqlalchemy.orm
from typing import List

#-----------------------------------------------------------------------

_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------
engine = sqlalchemy.create_engine(_DATABASE_URL, echo=True)
Base = sqlalchemy.orm.declarative_base()

#-----------------------------------------------------------------------

# creates table storing superadmin info
class SuperAdmin(Base):
    __tablename__ = 'superadmins'
    admin_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

def get_superadmins() -> List[SuperAdmin]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(SuperAdmin) # SELECT * FROM SuperAdmin
        return query.all()

#-----------------------------------------------------------------------

# creates table storing professor info
class Professor(Base):
    __tablename__ = 'professors'
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # prof net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

def get_profs():
     with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor) # SELECT * FROM Professor
        return query.all()

# gets prof first name given their netid
def get_prof_firstname(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor.first_name).filter(Professor.prof_id == prof_id).one_or_none()

        if query is None:
            return "Default"
        
        return query.all()

# gets prof info and the courses they teach in alphabetical order by prof first name
def get_all_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Professor.prof_id, Professor.first_name, Professor.last_name, CoursesProfs.course_id)
                .join(CoursesProfs, Professor.prof_id == CoursesProfs.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name))) 
        return query.all()

#-----------------------------------------------------------------------

# creates table storing course info
class Course(Base):
    __tablename__ = 'courses'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # e.g. SPA101
    course_code = sqlalchemy.Column(sqlalchemy.VARCHAR) # unique course code that gives students access
    course_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    course_description = sqlalchemy.Column(sqlalchemy.VARCHAR)
    owner = sqlalchemy.Column(sqlalchemy.VARCHAR)   # professor or superadmin netid
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    language = sqlalchemy.Column(sqlalchemy.VARCHAR)

def get_courses() -> List[Course]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Course) # SELECT * FROM Course
        return query.all()

#-----------------------------------------------------------------------

# creates table storing student info
class Student(Base):
    __tablename__ = 'students'
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # student net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# gets student info and the courses they belong to in alphabetical order by student first name
def get_all_students():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id, Student.first_name, Student.last_name, CoursesStudents.course_id)
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .order_by(sqlalchemy.asc(Student.first_name))) 
        return query.all()

# gets student first name based on their netid
def get_student_firstname(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Student.first_name).filter(Student.student_id == student_id).one_or_none()

        if query is None:
            return "Default"
        
        return query.all()

#-----------------------------------------------------------------------

# creates table mapping courses to professors
class CoursesProfs(Base):
    __tablename__ = 'coursesprofs'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# get all courses and the professors that teach them
def get_coursesprofs():
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(CoursesProfs.course_id, CoursesProfs.prof_id)
        return query.all()

#-----------------------------------------------------------------------

# creates table mapping courses to students
class CoursesStudents(Base):
    __tablename__ = 'coursesstudents'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# gets all students in a course given course id
def get_students_by_course(course_id):
     with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id, Student.first_name, Student.last_name)
                 .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                 .filter(CoursesStudents.course_id == course_id))
        return query.all()

#-----------------------------------------------------------------------

# creates table storing assignment prompts
class Prompt(Base):
    __tablename__ = 'prompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    prompt_title = sqlalchemy.Column(sqlalchemy.VARCHAR)
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    deadline = sqlalchemy.Column(sqlalchemy.TIMESTAMP)
    past_deadline = sqlalchemy.Column(sqlalchemy.Boolean)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    num_turns = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# get all assignments for a given course
def get_assignments(course_id) -> List[Prompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Prompt.deadline, Prompt.past_deadline, Prompt.created_at)
                .filter(Prompt.course_id == course_id))
        return query.all()

#-----------------------------------------------------------------------

# creates table storing practice prompts
class PracticePrompt(Base):
    __tablename__ = 'practiceprompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    course_id = sqlalchemy.Column(sqlalchemy.Integer)
    prof_id = sqlalchemy.Column(sqlalchemy.Integer)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# get all practice prompts for a given course
def get_practice_prompts(course_id) -> List[Prompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(PracticePrompt.prompt_id, PracticePrompt.prompt_title, PracticePrompt.created_at)
                .filter(PracticePrompt.course_id == course_id))
        return query.all()

#-----------------------------------------------------------------------

# creates table storing student conversations with the chatbot
# we only store assignment conversations, not practice ones
class Conversation(Base):
    __tablename__ = 'conversations'
    conv_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    course_id = sqlalchemy.Column(sqlalchemy.Integer)
    student_id = sqlalchemy.Column(sqlalchemy.Integer)
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer)
    conv_text = sqlalchemy.Column(sqlalchemy.Text)
    score = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

def get_conversations() -> List[Conversation]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Conversation) # SELECT * FROM Conversation
        return query.all()

# gets the score given a student net id and the assignment id
def get_score_for_student(student_id, prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Conversation.score)
                .filter(Conversation.student_id == student_id and Conversation.prompt_id == prompt_id)) 

        return query.all()

# gets all student scores for an assignment given the assignment id
def get_all_scores(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Conversation.score)
                .filter(Conversation.prompt_id == prompt_id)) 

        return query.all()

#-----------------------------------------------------------------------

# check if user exists in students, profs, or superadmin tables
def in_students(user_id):
    with sqlalchemy.orm.Session(engine) as session:
        return session.query(Student.student_id).filter_by(student_id=user_id).first() is not None

def in_profs(user_id):
    with sqlalchemy.orm.Session(engine) as session:
        return session.query(Professor.prof_id).filter_by(prof_id=user_id).first() is not None

def in_superadmins(user_id: str):
    with sqlalchemy.orm.Session(engine) as session:
        return session.query(SuperAdmin.admin_id).filter_by(admin_id=user_id).first() is not None
    
#-----------------------------------------------------------------------

# return user type or None if not found
def check_user_type(user_id: str):
    if in_students(user_id):
        return "Student"
    if in_profs(user_id):
        return "Professor"
    if in_superadmins(user_id):
        return "SuperAdmin"
    return None

#-----------------------------------------------------------------------

# get all courses that a professor teaches given the prof_id
def get_professor_courses(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        my_courses = session.query(CoursesProfs).filter(CoursesProfs.prof_id == prof_id).all()

        course_data = []
        for course_prof in my_courses:
            course = session.query(Course).filter(Course.course_id == course_prof.course_id).first()
            if course:
                course_data.append({
                    'course_id': course.course_id,
                    'course_name': course.course_name
                })

        return course_data
#-----------------------------------------------------------------------

# get all courses that a student is in given their student id
def get_student_courses(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        my_courses = session.query(CoursesStudents).filter(CoursesStudents.student_id == student_id).all()

        course_data = []
        for student in my_courses:
            course = session.query(Course).filter(Course.course_id == student.course_id).first()
            if course:
                course_data.append({
                    'course_id': course.course_id,
                    'course_name': course.course_name
                })

        return course_data
#-----------------------------------------------------------------------

# Function to enroll a student in a course using the course code
def enroll_student_in_course(student_id, course_code):
    with sqlalchemy.orm.Session(engine) as session:
        # Retrieve the course using the course code
        course = session.query(Course).filter_by(course_code=course_code).first()
        if not course:
            return {"status": "error", "message": "Invalid course code"}

        # Check if the student is already enrolled
        existing_enrollment = session.query(CoursesStudents).filter_by(course_id=course.course_id, student_id=student_id).first()
        if existing_enrollment:
            return {"status": "error", "message": "Already enrolled in this course"}

        # Enroll the student in the course
        new_enrollment = CoursesStudents(course_id=course.course_id, student_id=student_id)
        session.add(new_enrollment)
        session.commit()

        return {"status": "success", "message": "Course joined successfully"}

#-----------------------------------------------------------------------
