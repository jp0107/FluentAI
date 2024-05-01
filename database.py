#-----------------------------------------------------------------------
# database.py
# Authors: Irene Kim, Jessie Wang, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
import sqlalchemy
import sqlalchemy.orm
import pytz
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
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

def get_superadmins() -> List[SuperAdmin]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(SuperAdmin) # SELECT * FROM SuperAdmin
        return query.all()
    
def get_superadmins_roster():
    with sqlalchemy.orm.Session(engine) as session:
        # Query to select admin_id, first_name, and last_name from SuperAdmin table
        query = session.query(SuperAdmin.admin_id, SuperAdmin.first_name, SuperAdmin.last_name)
        results = query.all()

        if not results:
            return None

        # Format query results to match front-end expectations
        admins = []

        for admin_id, first_name, last_name in results:
            # Concatenate first and last name into a single 'name'
            full_name = f"{first_name} {last_name}"
            admins.append({
                'net_id': admin_id,  # Changed key to 'net_id'
                'name': full_name    # Changed key to 'name'
            })

        return admins

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
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

def get_profs():
     with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor) # SELECT * FROM Professor
        return query.all()

# get all professors for a given course (FOR PROF ROSTER PAGE)
def get_profs_for_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        try:
            # Query for professors associated with the course
            profs_query = (
                session.query(
                    Professor.prof_id,
                    Professor.first_name,
                    Professor.last_name
                )
                .join(CoursesProfs, Professor.prof_id == CoursesProfs.prof_id)
                .filter(CoursesProfs.course_id == course_id)
                .order_by(Professor.first_name, Professor.last_name)
            )
            professors = [
                {"prof_id": prof.prof_id, "first_name": prof.first_name, "last_name": prof.last_name}
                for prof in profs_query.all()
            ]

            # Query for superadmins associated with the course
            admins_query = (
                session.query(
                    SuperAdmin.admin_id.label('prof_id'),
                    SuperAdmin.first_name,
                    SuperAdmin.last_name
                )
                .join(CoursesProfs, SuperAdmin.admin_id == CoursesProfs.prof_id)
                .filter(CoursesProfs.course_id == course_id)
                .order_by(SuperAdmin.first_name, SuperAdmin.last_name)
            )
            superadmins = [
                {"prof_id": admin.prof_id, "first_name": admin.first_name, "last_name": admin.last_name}
                for admin in admins_query.all()
            ]

            # Combine both lists
            combined_results = professors + superadmins
            return combined_results

        except sqlalchemy.exc.SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to fetch course staff due to a database error: {str(e)}")



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

# check if a professor is the course owner
def check_if_owner(course_id, prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Check if there is a course record with the given course_id that is owned by the specified prof_id
        owner = session.query(Course).filter(
            Course.course_id == course_id,
            Course.owner == prof_id
        ).first()
        return owner is not None

# get language for course
def get_language(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Course.language)
                .filter(Course.course_id == course_id)) 
        return query.all()    

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

#-----------------------------------------------------------------------

# creates table storing student info
class Student(Base):
    __tablename__ = 'students'
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # student net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# get student info and the courses they belong to in alphabetical order by student first name
def get_all_students():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id, Student.first_name, Student.last_name, CoursesStudents.course_id)
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name))) 
        return query.all()

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

# get courses and professors for each one (FOR ADMIN COURSES PAGE)
def get_courses_and_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, Professor.first_name, Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(CoursesProfs.course_id))
        
        results = query.all()
        
        if not results:
            print("No courses fetched from database.")
            return {}

        # format query results
        courses = {}

        for course_id, first_name, last_name in results:
            if course_id not in courses:
                courses[course_id] = {'course_id': course_id, 'professors': []}
            courses[course_id]['professors'].append(f"{first_name} {last_name}")

        print("success")

        return courses

# get prof info (FOR ADMIN PROFESSORS PAGE)
def get_prof_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, CoursesProfs.prof_id, Professor.first_name, Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name), sqlalchemy.asc(Professor.last_name)))
        
        results = query.all()
        
        if not results:
            return None

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

# get student info (FOR ADMIN STUDENTS PAGE)
def get_student_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesStudents.course_id, CoursesStudents.student_id, Student.first_name, Student.last_name)
                .join(Student, CoursesStudents.student_id == Student.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name)))
        
        results = query.all()
        
        if not results:
            return None

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
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    num_turns = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    assignment_description = sqlalchemy.Column(sqlalchemy.VARCHAR)

# get prompt title by id
def get_prompt_title(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        
        query = (session.query(Prompt.prompt_title).filter(Prompt.prompt_id == prompt_id))

        return query.all()

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
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer)
    conv_text = sqlalchemy.Column(sqlalchemy.Text)
    score = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    prof_scores = sqlalchemy.Column(sqlalchemy.Integer)

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

# get assignments for prof (FOR PROF SCORES PAGE)
def get_assignments_for_prof(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        assignments = session.query(
            Prompt.prompt_id,
            Prompt.prompt_title,
            Prompt.deadline
        ).filter(Prompt.course_id == course_id).order_by(sqlalchemy.asc(Prompt.deadline)).all()

        return assignments

# gets the course assignments and their scores for each given a student id
def get_assignments_and_scores_for_student(course_id, student_id):
    with sqlalchemy.orm.Session(engine) as session:
        # check if the student exists in the database
        # student_exists = session.query(sqlalchemy.exists().where(Student.student_id == student_id)).scalar()
        # if not student_exists:
        #     return None

        query = (session.query(Prompt.prompt_id, Prompt.prompt_title, Conversation.conv_id, Conversation.score)
                 .outerjoin(Conversation, sqlalchemy.and_(Conversation.prompt_id == Prompt.prompt_id, Conversation.student_id == student_id))
                 .filter(Prompt.course_id == course_id)
                 .order_by(sqlalchemy.asc(Prompt.created_at)))

        results = query.all()
        return results if results else None

# gets all student scores in alphabetical order for an assignment given the assignment id (FOR PROF SCORES PAGE)
# def get_all_scores(prompt_id):
#     with sqlalchemy.orm.Session(engine) as session:

#         query = (session.query(
#                     sqlalchemy.func.concat(Student.first_name, ' ', Student.last_name).label('student_id'), 
#                     Conversation.conv_id, 
#                     Conversation.score)
#                  .join(CoursesStudents, CoursesStudents.student_id == Student.student_id)
#                  .join(Prompt, Prompt.course_id == CoursesStudents.course_id)
#                  .outerjoin(Conversation, sqlalchemy.and_(
#                      Conversation.student_id == Student.student_id,
#                      Conversation.prompt_id == Prompt.prompt_id))
#                  .filter(Prompt.prompt_id == prompt_id)
#                  .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name)))

#         results = query.all()

#         return results 

def get_all_scores(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(
                    CoursesStudents.student_id,
                    Conversation.conv_id, 
                    Conversation.score)
                 .join(Prompt, CoursesStudents.course_id == Prompt.course_id)
                 .outerjoin(Conversation, sqlalchemy.and_(
                     Conversation.student_id == CoursesStudents.student_id,
                     Conversation.prompt_id == prompt_id))
                 .filter(Prompt.prompt_id == prompt_id))

        results = query.all()
        return results

# get conversation history given a conv_id
def get_conversation(conv_id):
    with sqlalchemy.orm.Session(engine) as session:

        query = (session.query(Prompt.prompt_title, Conversation.conv_text)
                 .outerjoin(Conversation, sqlalchemy.and_(
                     Conversation.prompt_id == Prompt.prompt_id, 
                     Conversation.conv_id == conv_id 
                 ))
                 .filter(Conversation.conv_id == conv_id))

        results = query.all()
        return results

#-----------------------------------------------------------------------

# check if user exists in students, profs, or superadmin tables
def in_students(user_id):
    with sqlalchemy.orm.Session(engine) as session:
        return session.query(Student.student_id).filter_by(student_id=user_id).first() is not None

def in_profs(user_id):
    with sqlalchemy.orm.Session(engine) as session:
        return session.query(Professor.prof_id).filter_by(prof_id=user_id).first() is not None

def in_superadmins(user_id):
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

# check student enrollment in a course
def check_student_in_course(course_id, student_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Directly check for an existing enrollment record
        enrollment = session.query(CoursesStudents).filter(
            CoursesStudents.course_id == course_id,
            CoursesStudents.student_id == student_id
        ).first()

        # Return True if the enrollment exists, False otherwise
        return enrollment is not None

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
    est = pytz.timezone('America/New_York')
    with sqlalchemy.orm.Session(engine) as session:
        now_utc = datetime.now(pytz.utc)
        now_est = now_utc.astimezone(est)
        assignments = session.query(
            Prompt.prompt_id,
            Prompt.prompt_title,
            Prompt.prompt_text,
            Prompt.deadline,
            Prompt.num_turns,
            Prompt.created_at,
            Prompt.assignment_description
        ).filter(Prompt.course_id == course_id).order_by(sqlalchemy.asc(Prompt.deadline)).all()

        current_assignments = []
        past_assignments = []
        for assignment in assignments:
            if assignment.deadline:
                local_deadline = est.localize(assignment.deadline.replace(tzinfo=None))  # Assume deadline is stored in UTC
            else:
                local_deadline = None

            formatted_deadline = local_deadline.strftime('%m/%d/%Y %I:%M%p') if local_deadline else 'No deadline set'
            
            assignment_info = {
                'prompt_id': assignment.prompt_id,
                'prompt_title': assignment.prompt_title,
                'prompt_text': assignment.prompt_text,
                'deadline': formatted_deadline,
                'num_turns': assignment.num_turns,
                'created_at': assignment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'description': assignment.assignment_description
            }
            if assignment.deadline is None or assignment.deadline > now_est:
                current_assignments.append(assignment_info)
            else:
                past_assignments.append(assignment_info)

        return {'current_assignments': current_assignments, 'past_assignments': past_assignments}
#-----------------------------------------------------------------------
def get_assignments_for_student(student_id, course_id):
    est = pytz.timezone('America/New_York')
    with sqlalchemy.orm.Session(engine) as session:
        now_utc = datetime.now(pytz.utc)  # Get the current time in UTC
        now_est = now_utc.astimezone(est)  # Convert UTC time to EST

       # Define the subquery for the completed status
        completed_subquery = sqlalchemy.sql.exists().where(
            Conversation.student_id == student_id,
            Conversation.course_id == course_id,
            Conversation.prompt_id == Prompt.prompt_id
        ).label('completed')
        assignments = session.query(
            Prompt.prompt_id,
            Prompt.prompt_title,
            Prompt.deadline,
            Prompt.created_at,
            Prompt.assignment_description,
            completed_subquery  # This already behaves as a scalar subquery
        ).filter(Prompt.course_id == course_id).order_by(sqlalchemy.asc(Prompt.deadline)).all()
        return categorize_assignments(assignments, now_est)
#-----------------------------------------------------------------------

def categorize_assignments(assignments, now):
    current_assignments = []
    past_assignments = []
    for a in assignments:
        # Assume deadline is stored in UTC and convert to EST
        local_deadline = pytz.utc.localize(a.deadline).astimezone(pytz.timezone('America/New_York')) if a.deadline else None

        assignment_tuple = (
            a.prompt_id,
            a.prompt_title,
            local_deadline,  # Keep as datetime object
            a.created_at,
            a.assignment_description,
            a.completed
        )

        if local_deadline is None or local_deadline > now:
            current_assignments.append(assignment_tuple)
        else:
            past_assignments.append(assignment_tuple)

    return current_assignments, past_assignments
    
#-----------------------------------------------------------------------

def get_students_for_course(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        try:
            # Query for professors associated with the course
            profs_query = (
                session.query(
                    Professor.prof_id.label('student_id'),
                    Professor.first_name,
                    Professor.last_name
                )
                .join(CoursesStudents, Professor.prof_id == CoursesStudents.student_id)
                .filter(CoursesStudents.course_id == course_id)
                .order_by(Professor.first_name, Professor.last_name)
            )
            professors = [
                {"student_id": prof.student_.id, "first_name": prof.first_name, "last_name": prof.last_name}
                for prof in profs_query.all()
            ]

            # Query for superadmins associated with the course
            admins_query = (
                session.query(
                    SuperAdmin.admin_id.label('student_id'),
                    SuperAdmin.first_name,
                    SuperAdmin.last_name
                )
                .join(CoursesStudents, SuperAdmin.admin_id == CoursesStudents.student_id)
                .filter(CoursesStudents.course_id == course_id)
                .order_by(SuperAdmin.first_name, SuperAdmin.last_name)
            )
            superadmins = [
                {"student_id": admin.student_id, "first_name": admin.first_name, "last_name": admin.last_name}
                for admin in admins_query.all()
            ]

            # Query for students associated with the course
            students_query = (
                session.query(
                    Student.student_id,
                    Student.first_name,
                    Student.last_name
                )
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .filter(CoursesStudents.course_id == course_id)
                .order_by(Student.first_name, Student.last_name)
            )
            students = [
                {"student_id": student.student_id, "first_name": student.first_name, "last_name": student.last_name}
                for student in students_query.all()
            ]

            # Combine all results
            combined_results = professors + superadmins + students
            return combined_results

        except sqlalchemy.exc.SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to fetch course participants due to a database error: {str(e)}")


#-----------------------------------------------------------------------

def fetch_professors_and_courses():
    with sqlalchemy.orm.Session(engine) as session:
        try:
            # Fetching professors linked to courses
            profs_query = session.query(
                Professor.prof_id,
                Professor.first_name,
                Professor.last_name,
                CoursesProfs.course_id
            ).join(
                CoursesProfs, Professor.prof_id == CoursesProfs.prof_id
            ).order_by(Professor.first_name, Professor.last_name)

            # Fetching superadmins linked to courses
            admins_query = session.query(
                SuperAdmin.admin_id,
                SuperAdmin.first_name,
                SuperAdmin.last_name,
                CoursesProfs.course_id
            ).join(
                CoursesProfs, SuperAdmin.admin_id == CoursesProfs.prof_id
            ).order_by(SuperAdmin.first_name, SuperAdmin.last_name)

            professors = [
                {"net_id": prof.prof_id, "name": f"{prof.first_name} {prof.last_name}", "courses": [prof.course_id]}
                for prof in profs_query.all()
            ]

            superadmins = [
                {"net_id": admin.admin_id, "name": f"{admin.first_name} {admin.last_name}", "courses": [admin.course_id]}
                for admin in admins_query.all()
            ]

            # Combine and return results
            return professors + superadmins

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to fetch data due to: {str(e)}")

#-----------------------------------------------------------------------

def fetch_students_and_courses():
    with sqlalchemy.orm.Session(engine) as session:
        try:
            # Fetching students linked to courses
            students_query = session.query(
                Student.student_id.label('id'),
                Student.first_name,
                Student.last_name,
                CoursesStudents.course_id
            ).join(
                CoursesStudents, Student.student_id == CoursesStudents.student_id
            ).order_by(Student.first_name, Student.last_name)

            # Fetching professors linked to courses
            professors_query = session.query(
                Professor.prof_id.label('id'),
                Professor.first_name,
                Professor.last_name,
                CoursesStudents.course_id
            ).join(
                CoursesStudents, Professor.prof_id == CoursesStudents.student_id
            ).order_by(Professor.first_name, Professor.last_name)

            # Fetching superadmins linked to courses
            superadmins_query = session.query(
                SuperAdmin.admin_id.label('id'),
                SuperAdmin.first_name,
                SuperAdmin.last_name,
                CoursesStudents.course_id
            ).join(
                CoursesStudents, SuperAdmin.admin_id == CoursesStudents.student_id
            ).order_by(SuperAdmin.first_name, SuperAdmin.last_name)

            # Combine all results using union_all
            combined_query = students_query.union_all(professors_query).union_all(superadmins_query)
            results = combined_query.all()

            # Convert results into a list of dictionaries
            merged_results = [
                {
                    "id": result.id,
                    "name": f"{result.first_name} {result.last_name}",
                    "courses": [result.course_id]
                }
                for result in results
            ]

            return merged_results

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to fetch data due to: {str(e)}")
#-----------------------------------------------------------------------
def check_prof_in_course(course_id, prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Directly check for an existing association record between the professor and the course
        association = session.query(CoursesProfs).filter(
            CoursesProfs.course_id == course_id,
            CoursesProfs.prof_id == prof_id
        ).first()

        # Return True if the association exists, False otherwise
        return association is not None