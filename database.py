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

def get_profs() -> List[Professor]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor) # SELECT * FROM Professor
        return query.all()

def get_prof_firstname(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor.first_name).filter(Professor.prof_id == prof_id).one_or_none()

        if query is None:
            return "Default"
        
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

def get_students() -> List[Student]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Student) # SELECT * FROM Student
        return query.all()

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

def get_coursesprofs() -> List[CoursesProfs]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(CoursesProfs) # SELECT * FROM CoursesProfs
        return query.all()

#-----------------------------------------------------------------------

# creates table mapping courses to students
class CoursesStudents(Base):
    __tablename__ = 'coursesstudents'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

def get_coursesstudents() -> List[CoursesStudents]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(CoursesStudents) # SELECT * FROM CoursesStudents
        return query.all()

def get_students_by_course(course_id):
     with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.first_name, Student.last_name)
                 .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                 .filter(CoursesStudents.course_id == course_id))
        full_names = [f"{first} {last}" for first, last in query.all()]
        return full_names

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

def get_prompts() -> List[Prompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Prompt) # SELECT * FROM Prompt
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

def get_practiceprompts() -> List[PracticePrompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(PracticePrompt) # SELECT * FROM PracticePrompt
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