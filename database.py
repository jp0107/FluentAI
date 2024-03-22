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
_engine = sqlalchemy.create_engine(_DATABASE_URL, echo=True)
Base = sqlalchemy.orm.declarative_base()

#-----------------------------------------------------------------------

# creates table storing superadmin info
class SuperAdmin(Base):
    __tablename__ = 'superadmins'
    admin_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_superadmins() -> List[SuperAdmin]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(SuperAdmin) # SELECT * FROM SuperAdmin
        return query.all()

#-----------------------------------------------------------------------

# creates table storing professor info
class Professor(Base):
    __tablename__ = 'professors'
    prof_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True) # prof net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_profs() -> List[Professor]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(Professor) # SELECT * FROM Professor
        return query.all()

#-----------------------------------------------------------------------

# creates table storing course info
class Course(Base):
    __tablename__ = 'courses'
    course_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True) # e.g. SPA101
    course_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    course_description = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_courses() -> List[Course]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(Course) # SELECT * FROM Course
        return query.all()

#-----------------------------------------------------------------------

# creates table storing student info
class Student(Base):
    __tablename__ = 'students'
    student_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True) # student net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_students() -> List[Student]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(Student) # SELECT * FROM Student
        return query.all()

#-----------------------------------------------------------------------

# creates table mapping courses to professors
class CoursesProfs(Base):
    __tablename__ = 'coursesprofs'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

def get_coursesprofs() -> List[CoursesProfs]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(CoursesProfs) # SELECT * FROM CoursesProfs
        return query.all()

#-----------------------------------------------------------------------

# creates table mapping courses to students
class CoursesStudents(Base):
    __tablename__ = 'coursesstudents'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

def get_coursesstudents() -> List[CoursesStudents]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(CoursesStudents) # SELECT * FROM CoursesStudents
        return query.all()

#-----------------------------------------------------------------------

# creates table storing assignment prompts
class Prompt(Base):
    __tablename__ = 'prompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    prompt_title = sqlalchemy.Column(sqlalchemy.VARCHAR)
    course_id = sqlalchemy.Column(sqlalchemy.Integer)
    prof_id = sqlalchemy.Column(sqlalchemy.Integer)
    is_live = sqlalchemy.Column(sqlalchemy.Boolean)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_prompts() -> List[Prompt]:
    with sqlalchemy.orm.Session(_engine) as session:
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
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_practiceprompts() -> List[PracticePrompt]:
    with sqlalchemy.orm.Session(_engine) as session:
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
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

def get_conversations() -> List[Conversation]:
    with sqlalchemy.orm.Session(_engine) as session:
        query = session.query(Conversation) # SELECT * FROM Conversation
        return query.all()

#-----------------------------------------------------------------------
# testing
# Base.metadata.create_all(_engine)

# Session = sqlalchemy.orm.sessionmaker(bind=_engine)
# session = Session()

# new_prof = Professor(
#     prof_id = 1234,
#     first_name = "Bob",
#     last_name = "Dondero",
#     email = "bobdondero@cs.princeton.edu",
#     created_at = sqlalchemy.func.now()
# )

# session.add(new_prof)

# professors = session.query(Professor).all()

# for prof in professors:
#     print(prof.first_name)

# session.commit()
# session.close()