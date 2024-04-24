#-----------------------------------------------------------------------
# database.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sqlalchemy
import sqlalchemy.orm
from typing import List
from datetime import datetime, timedelta
import logging

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

# gets admin first name given their netid
def get_admin_firstname(admin_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(SuperAdmin.first_name).filter(SuperAdmin.admin_id == admin_id).one_or_none()

        if query is None:
            return "Default"
        
        return query[0]

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

# get default professor roster
def get_default_prof_roster():
    return [
        ('bd0101', 'Bob', 'Dondero')
    ]

# get all professors for a given course (FOR PROF ROSTER PAGE)
def get_profs_in_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Professor.prof_id, Professor.first_name, Professor.last_name)
                .join(CoursesProfs, Professor.prof_id == CoursesProfs.prof_id)
                .filter(CoursesProfs.course_id == course_id)
                .order_by(sqlalchemy.asc(Professor.first_name), sqlalchemy.asc(Professor.last_name))) 
        results = query.all()
        return results if results else get_default_prof_roster()

# gets prof first name given their netid
def get_prof_firstname(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor.first_name).filter(Professor.prof_id == prof_id).one_or_none()

        if query is None:
            return "Default"
        
        return query[0]

# gets prof info and the courses they teach in alphabetical order by prof first name
def get_all_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Professor.prof_id, Professor.first_name, Professor.last_name, CoursesProfs.course_id)
                .join(CoursesProfs, Professor.prof_id == CoursesProfs.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name), sqlalchemy.asc(Professor.last_name))) 
        return query.all()

#-----------------------------------------------------------------------

# creates table storing course info
class Course(Base):
    __tablename__ = 'courses'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # e.g. SPA101
    course_code = sqlalchemy.Column(sqlalchemy.VARCHAR) # unique course code that gives students access
    course_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    owner = sqlalchemy.Column(sqlalchemy.VARCHAR)   # professor or superadmin netid
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    language = sqlalchemy.Column(sqlalchemy.VARCHAR)

def get_courses() -> List[Course]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Course) # SELECT * FROM Course
        return query.all()

# get course code given course_id
def get_course_code(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Course.course_code)
                .filter(Course.course_id == course_id)) 
        return query.all()

# edit course code
def edit_course_code(course_id, new_course_code):
    with sqlalchemy.orm.Session(engine) as session:
        course = session.query(Course).filter(Course.course_id == course_id).first()

        if course:
            course.course_code = new_course_code
            session.commit()
            return True
        else:
            return False 

# # delete course
# def delete_course(course_id):
#     with Session() as session:
#         try:
#             # Delete associated entries from CoursesProfs
#             session.query(CoursesProfs).filter(CoursesProfs.course_id == course_id).delete(synchronize_session='fetch')
#             # Delete associated entries from CoursesStudents
#             session.query(CoursesStudents).filter(CoursesStudents.course_id == course_id).delete(synchronize_session='fetch')
#             # Delete the course entry
#             course_entry_to_delete = session.query(Course).filter(Course.course_id == course_id).one_or_none()
#             if course_entry_to_delete:
#                 session.delete(course_entry_to_delete)
#                 session.commit()
#                 return True
           
#                 session.commit()
#                 return False
#         except Exception as e:
#             session.rollback()
#             print(f"An error occurred: {e}")
#             return False

#-----------------------------------------------------------------------

# creates table storing student info
class Student(Base):
    __tablename__ = 'students'
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # student net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# get default student roster
def get_default_student_roster():
    return [
        ('ik1234', 'Irene', 'Kim'),
        ('tm0261', 'Tinney', 'Mak'),
        ('jp2024', 'Jonathan', 'Peixoto'),
        ('jw2003', 'Jessie', 'Wang')
    ]

# get student info and the courses they belong to in alphabetical order by student first name
def get_all_students():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id, Student.first_name, Student.last_name, CoursesStudents.course_id)
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name))) 
        return query.all()

# get all students in a given course (FOR PROF ROSTER PAGE)
def get_students_in_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id, Student.first_name, Student.last_name)
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .filter(CoursesStudents.course_id == course_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name))) 
        results = query.all()
        return results if results else get_default_student_roster()

# gets student first name based on their netid
def get_student_firstname(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Student.first_name).filter(Student.student_id == student_id).one_or_none()

        if query is None:
            return "Default"
        
        return query[0]

# delete student
def delete_student(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        try:
            # delete associated entries from CoursesStudents first
            session.query(CoursesStudents).filter(CoursesStudents.student_id == student_id).delete(synchronize_session='fetch')

            # delete the course entry
            student_to_delete = session.query(Student).filter(Student.student_id == student_id).one_or_none()
            if student_to_delete:
                session.delete(student_to_delete)
                session.commit()
                return True
            else:
                session.commit()  
                return False
        except Exception as e:
            session.rollback()  
            print(f"An error occurred: {e}")
            return False

#-----------------------------------------------------------------------

# creates table mapping courses to professors
class CoursesProfs(Base):
    __tablename__ = 'coursesprofs'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# get default courses and profs
def get_default_courses_and_profs():
    return [
        ('SPA100', 'Irene', 'Kim'),
        ('SPA100', 'Tinney', 'Mak'),
        ('SPA200', 'Jonathan', 'Peixoto'),
        ('SPA300', 'Jessie', 'Wang')
    ]

# get default profs
def get_default_profs():
    return [
        ('SPA100', 'ik1234', 'Irene', 'Kim'),
        ('SPA200', 'ik1234', 'Irene', 'Kim'),
        ('SPA200', 'jp2024', 'Jonathan', 'Peixoto'),
        ('SPA300', 'jw2003', 'Jessie', 'Wang')
    ]

# get courses and professors for each one (FOR ADMIN COURSES PAGE)
def get_courses_and_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, Professor.first_name, Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(CoursesProfs.course_id))
        
        results = query.all()
        
        if not results:
            results = get_default_courses_and_profs()

        # format query results
        courses = {}

        for course_id, first_name, last_name in results:
            if course_id not in courses:
                courses[course_id] = {'course_id': course_id, 'professors': []}
            courses[course_id]['professors'].append(f"{first_name} {last_name}")

        return courses

# get prof info (FOR ADMIN PROFESSORS PAGE)
def get_prof_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, CoursesProfs.prof_id, Professor.first_name, Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name), sqlalchemy.asc(Professor.last_name)))
        
        results = query.all()
        
        if not results:
            results = get_default_profs()

        # format query results
        profs = {}

        for course_id, prof_id, first_name, last_name in results:
            if prof_id not in profs:
                profs[prof_id] = {'prof_id': prof_id, 'prof_name': f"{first_name} {last_name}", 'courses': []}
            profs[prof_id]['courses'].append(course_id)

        return profs

#-----------------------------------------------------------------------

# creates table mapping courses to students
class CoursesStudents(Base):
    __tablename__ = 'coursesstudents'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# get default students
def get_default_students():
    return [
        ('SPA200', 'jp2024', 'Jonathan', 'Peixoto'),
        ('SPA300', 'jw2003', 'Jessie', 'Wang'),
        ('SPA500', 'jp2024', 'Jonathan', 'Peixoto')
    ]

# get student info (FOR ADMIN STUDENTS PAGE)
def get_student_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesStudents.course_id, CoursesStudents.student_id, Student.first_name, Student.last_name)
                .join(Student, CoursesStudents.student_id == Student.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name)))
        
        results = query.all()
        
        if not results:
            results = get_default_students()

        # format query results
        students = {}

        for course_id, student_id, first_name, last_name in results:
            if student_id not in students:
                students[student_id] = {'student_id': student_id, 'student_name': f"{first_name} {last_name}", 'courses': []}
            students[student_id]['courses'].append(course_id)

        return students

#-----------------------------------------------------------------------

# creates table storing assignment prompts
class Prompt(Base):
    __tablename__ = 'prompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    prompt_title = sqlalchemy.Column(sqlalchemy.VARCHAR)
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    deadline = sqlalchemy.Column(sqlalchemy.TIMESTAMP)
    past_deadline = sqlalchemy.Column(sqlalchemy.Boolean)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    num_turns = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    assignment_description = sqlalchemy.Column(sqlalchemy.VARCHAR)

# get default current assignments for student
def get_curr_student_default_assignments():
    now = datetime.now()
    return [
        (11111, 'Assignment 1: Café Fluent', now + timedelta(days=10), False, now, True),
        (22222, 'Assignment 2: Job Interview', now + timedelta(days=20), False, now, False),
        (33333, 'Assignment 3: Airport Troubles', now + timedelta(days=30), False, now, False)
    ]

# get default current assignments for prof
def get_curr_prof_default_assignments():
    now = datetime.now()
    return [
        (11111, 'Assignment 1: Café Fluent', now + timedelta(days=10), False, now),
        (22222, 'Assignment 2: Job Interview', now + timedelta(days=20), False, now),
        (33333, 'Assignment 3: Airport Troubles', now + timedelta(days=30), False, now)
    ]

# get default assignments for a course
def get_default_assignments():
    now = datetime.now()
    return [
        (11111, 'Assignment 1: Café Fluent', now + timedelta(days=10)),
        (22222, 'Assignment 2: Job Interview', now + timedelta(days=20)),
        (33333, 'Assignment 3: Airport Troubles', now + timedelta(days=30))
    ]

# get default past assignments
def get_past_default_assignments():
    now = datetime.now()
    return [(12345, 'Assignment 0: Say Hello', now - timedelta(days=3), True, now - timedelta(days=5))]

# get all current course assignments for a student, with the earliest deadline first (FOR STUDENT ASSIGNMENTS PAGE)
# mark whether assignment has been completed or not
def get_current_assignments_for_student(student_id, course_id):
    with sqlalchemy.orm.Session(engine) as session:
        
        subquery = (session.query(Conversation.prompt_id)
                    .filter(Conversation.student_id == student_id, Conversation.prompt_id == Prompt.prompt_id)
                    .exists()).label("completed")

        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Prompt.deadline, Prompt.past_deadline, Prompt.created_at, subquery)
                 .filter(Prompt.course_id == course_id, Prompt.past_deadline == False)
                 .order_by(sqlalchemy.asc(Prompt.deadline)))

        results = query.all()
        return results
# get all current assignments for a given course, with the earliest deadline first (FOR PROFESSOR ASSIGNMENTS PAGE)
def get_current_assignments_for_prof(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Prompt.deadline, Prompt.past_deadline, Prompt.created_at)
                .filter(Prompt.course_id == course_id, Prompt.past_deadline == False)
                .order_by(sqlalchemy.asc(Prompt.deadline)))

        results = query.all()

        return results if results else get_curr_prof_default_assignments()

# get all past assignments for a given course, with the most recent assignment first
def get_past_assignments(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Prompt.deadline, Prompt.past_deadline, Prompt.created_at)
                 .filter(Prompt.course_id == course_id, Prompt.past_deadline == True)  
                 .order_by(sqlalchemy.desc(Prompt.deadline))) 

        results = query.all()

        return results if results else get_past_default_assignments()

# get all asssignments for a course (FOR PROF SCORES PAGE)
def get_all_assignments_for_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        # check if course exists in the database
        course_exists = session.query(sqlalchemy.exists().where(Course.course_id == course_id)).scalar()
        if not course_exists:
            return get_default_assignments()

        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Prompt.deadline)
                .filter(Prompt.course_id == course_id)
                .order_by(sqlalchemy.asc(Prompt.deadline)))

        results = query.all()

        return results if results else get_default_assignments()

#-----------------------------------------------------------------------

# creates table storing practice prompts
class PracticePrompt(Base):
    __tablename__ = 'practiceprompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    course_id = sqlalchemy.Column(sqlalchemy.Integer)
    prof_id = sqlalchemy.Column(sqlalchemy.Integer)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# get default practice prompts
def get_default_practice():
    now = datetime.now()
    return [
        (98762, 'Assignment 0: Say Hello', now),
        (98765, 'Assignment 1: Café Fluent', now),
        (87654, 'Assignment 2: Job Interview', now),
        (76543, 'Assignment 3: Airport Troubles', now)
    ]

# get all practice prompts for a given course, ordered by most to least recently created
def get_practice_prompts(course_id) -> List[Prompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(PracticePrompt.prompt_id, PracticePrompt.prompt_title, PracticePrompt.created_at)
                .filter(PracticePrompt.course_id == course_id)
                .order_by(sqlalchemy.desc(PracticePrompt.created_at)))
        
        results = query.all()

        return results if results else get_default_practice()

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

# get default student scores for a course
def get_default_student_scores():
    return [
        (98762, 'Assignment 0: Say Hello', 1, 100),
        (98765, 'Assignment 1: Café Fluent', 2, 96),
        (87654, 'Assignment 2: Job Interview', 3, 25),
        (76543, 'Assignment 3: Airport Troubles', 4, None)
    ]

# get default scores for an assignment for each student in a course
def get_default_scores_for_assignment():
    return [
        ('Irene', 'Kim', 1, 100),
        ('Jonathan', 'Peixoto', 2, 25),
        ('Jessie', 'Wang', 3, None)
    ]

# get default conversation
def get_default_conversation():
    return [('Assignment 0: Default', 'Mi nueva casa está en una calle ancha que tiene muchos árboles. El piso de arriba de mi casa tiene tres dormitorios y un despacho para trabajar. El piso de abajo tiene una cocina muy grande, un comedor con una mesa y seis sillas, un salón con dos sofás verdes, una televisión y cortinas. Además, tiene una pequeña terraza con piscina donde puedo tomar el sol en verano.')]

# gets the course assignments and their scores for each given a student id
def get_assignments_and_scores_for_student(course_id, student_id):
    with sqlalchemy.orm.Session(engine) as session:
        # check if the student exists in the database
        student_exists = session.query(sqlalchemy.exists().where(Student.student_id == student_id)).scalar()
        if not student_exists:
            return get_default_student_scores()

        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Conversation.conv_id, Conversation.score)
                 .outerjoin(Conversation, sqlalchemy.and_(Conversation.prompt_id == Prompt.prompt_id, Conversation.student_id == student_id))
                 .filter(Prompt.course_id == course_id)
                 .order_by(sqlalchemy.asc(Prompt.created_at)))

        results = query.all()
        return results if results else get_default_student_scores()

# gets all student scores in alphabetical order for an assignment given the assignment id (FOR PROF SCORES PAGE)
def get_all_scores(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:

        # check if the prompt exists in the database
        prompt_exists = session.query(sqlalchemy.exists().where(Prompt.prompt_id == prompt_id)).scalar()
        if not prompt_exists:
            return get_default_scores_for_assignment()

        query = (session.query(Student.first_name, Student.last_name, Conversation.id, Conversation.score)
                .outerjoin(Conversation, sqlalchemy.and_(Conversation.student_id == Student.student_id, Conversation.prompt_id == prompt_id))
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name))) 

        results = query.all()

        return results if results else get_default_scores_for_assignment()

# get conversation history given a conv_id
def get_conversation(course_id, student_id, conv_id):
    with sqlalchemy.orm.Session(engine) as session:
        # check if the student exists in the database
        student_exists = session.query(sqlalchemy.exists().where(Student.student_id == student_id)).scalar()
        if not student_exists:
            return get_default_conversation()

        query = (session.query(Prompt.prompt_title, Conversation.conv_text)
                 .outerjoin(Conversation, sqlalchemy.and_(
                     Conversation.prompt_id == Prompt.prompt_id, 
                     Conversation.conv_id == conv_id 
                 ))
                 .filter(Prompt.course_id == course_id))

        results = query.one_or_none()
        return results if results else get_default_conversation()

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

def get_prompt_by_id(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        prompt = session.query(Prompt).filter(Prompt.prompt_id == prompt_id).first()
        return prompt

#-----------------------------------------------------------------------
def get_assignments_for_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Query to get all prompts for a given course ID
        assignments = session.query(Prompt).filter(Prompt.course_id == course_id).all()
        course_assignments = []
        for assignment in assignments:
            assignment_data = {
            'prompt_id': assignment.prompt_id,
            'prompt_title': assignment.prompt_title,
            'prompt_text': assignment.prompt_text,
            'deadline': assignment.deadline if assignment.deadline else None,
            'num_turns': assignment.num_turns,
            'created_at': assignment.created_at,
            'past_deadline': assignment.past_deadline
            }
            course_assignments.append(assignment_data)
        return course_assignments
#-----------------------------------------------------------------------
def get_assignments_for_student(student_id, course_id):
    with sqlalchemy.orm.Session(engine) as session:
        now = datetime.now()
        completed_subquery = session.query(Conversation.conv_id).filter(
            Conversation.student_id == student_id,
            Conversation.course_id == course_id,
            Conversation.prompt_id == Prompt.prompt_id
        ).exists().label('completed')
        assignments = session.query(
            Prompt.prompt_id,
            Prompt.prompt_title,
            Prompt.deadline,
            Prompt.created_at,
            completed_subquery.as_scalar().label('completed')
        ).filter(Prompt.course_id == course_id).order_by(sqlalchemy.asc(Prompt.deadline)).all()

        return categorize_assignments(assignments, now)
#-----------------------------------------------------------------------

def categorize_assignments(assignments, now):
    current_assignments = []
    past_assignments = []
    for a in assignments:
        # Tuple construction
        assignment_tuple = (a.prompt_id, a.prompt_title, a.deadline, a.created_at, a.completed)

        if a.deadline > now:
            current_assignments.append(assignment_tuple)
        else:
            past_assignments.append(assignment_tuple)

    return current_assignments, past_assignments
    
#-----------------------------------------------------------------------

def get_past_assignments_for_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        assignments = (session.query(Prompt)
                    .filter(Prompt.course_id == course_id, Prompt.past_deadline == True)
                    .order_by(sqlalchemy.desc(Prompt.deadline))).all()

        past_assignments = []

        # default case
        if not assignments:
            assignments = get_full_past_default_assignments()
            assignment_data = {
                'prompt_id': assignments[0][0],
                'prompt_title': assignments[0][1],
                'prompt_text': assignments[0][2],
                'deadline': assignments[0][3],
                'num_turns': assignments[0][4],
                'created_at': assignments[0][5],
                'past_deadline': assignments[0][6]
            }
            past_assignments.append(assignment_data)
            return past_assignments

        # normal case
        for assignment in assignments:
            assignment_data = {
            'prompt_id': assignment.prompt_id,
            'prompt_title': assignment.prompt_title,
            'prompt_text': assignment.prompt_text,
            'deadline': assignment.deadline if assignment.deadline else None,
            'num_turns': assignment.num_turns,
            'created_at': assignment.created_at,
            'past_deadline': assignment.past_deadline
            }
            past_assignments.append(assignment_data)
        return past_assignments

# get default past assignments with full info (FOR PROF ASSIGNMENTS PAGE)
def get_full_past_default_assignments():
    now = datetime.now()
    return [(12345, 'Assignment 0: Say Hello', "Say hello to the student", now - timedelta(days=3), 5, now - timedelta(days=10), True)]

#-----------------------------------------------------------------------

