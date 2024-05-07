#-----------------------------------------------------------------------
# database.py
# Authors: Jessie Wang, Irene Kim, Jonathan Peixoto, Tinney Mak
#-----------------------------------------------------------------------

import os
from typing import List
from datetime import datetime, timezone
import sqlalchemy
import sqlalchemy.orm
import pytz
import numpy as np

#-----------------------------------------------------------------------

_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------
engine = sqlalchemy.create_engine(_DATABASE_URL, echo=True)
Base = sqlalchemy.orm.declarative_base()

#-----------------------------------------------------------------------

# Creates table storing superadmin info
class SuperAdmin(Base):
    __tablename__ = 'superadmins'
    admin_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP,
                                    default=sqlalchemy.sql.func.now())

# Gets all superadmins
def get_superadmins() -> List[SuperAdmin]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(SuperAdmin) # SELECT * FROM SuperAdmin
        return query.all()

# Gets super admin roster
def get_superadmins_roster():
    with sqlalchemy.orm.Session(engine) as session:
        # Query to select admin info from SuperAdmin table
        query = session.query(SuperAdmin.admin_id,
                            SuperAdmin.first_name,
                            SuperAdmin.last_name)
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

# Gets super admin first name given their netid
def get_admin_firstname(admin_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(SuperAdmin.first_name).filter(
            SuperAdmin.admin_id == admin_id).one_or_none()

        if query is None:
            return "Default"

        return query[0]

#-----------------------------------------------------------------------

# Creates table storing professor info
class Professor(Base):
    __tablename__ = 'professors'
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP,
                                    default=sqlalchemy.sql.func.now())

# Gets profs
def get_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor) # SELECT * FROM Professor
        return query.all()

# Gets all professors for a given course (FOR PROF ROSTER PAGE)
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
                .join(CoursesProfs,
                    Professor.prof_id == CoursesProfs.prof_id)
                .filter(CoursesProfs.course_id == course_id)
                .order_by(Professor.first_name, Professor.last_name)
            )
            professors = [
                {"prof_id": prof.prof_id,
                "first_name": prof.first_name,
                "last_name": prof.last_name}
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
                {"prof_id": admin.prof_id,
                "first_name": admin.first_name,
                "last_name": admin.last_name}
                for admin in admins_query.all()
            ]

            # Combine both lists
            combined_results = professors + superadmins
            return combined_results

        except sqlalchemy.exc.SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to fetch course staff due to a database error: {str(e)}")


# Gets prof first name given their netid
def get_prof_firstname(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Professor.first_name).filter(
            Professor.prof_id == prof_id).one_or_none()

        if query is None:
            return "Default"
        
        return query[0]

# Gets prof info and the courses they teach in alphabetical order by prof first name
def get_all_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Professor.prof_id,
                            Professor.first_name,
                            Professor.last_name,
                            CoursesProfs.course_id)
                .join(CoursesProfs, Professor.prof_id == CoursesProfs.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name),
                        sqlalchemy.asc(Professor.last_name))) 
        return query.all()

#-----------------------------------------------------------------------

# Creates table storing course info
class Course(Base):
    __tablename__ = 'courses'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # e.g. SPA101
    course_code = sqlalchemy.Column(sqlalchemy.VARCHAR) 
    course_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    owner = sqlalchemy.Column(sqlalchemy.VARCHAR)  
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    language = sqlalchemy.Column(sqlalchemy.VARCHAR)

# Checks if a course exists
def check_if_course_exists(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Course.course_id).filter(
            sqlalchemy.func.upper(Course.course_id) == course_id.upper()).first()
        return query is not None

# Checks if a professor is the course owner
def check_if_owner(course_id, prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        owner = session.query(Course).filter(
            Course.course_id == course_id,
            Course.owner == prof_id
        ).first()
        return owner is not None

# Gets language for course
def get_language(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Course.language)
                .filter(Course.course_id == course_id)) 
        return query.all()    

# Gets list of all courses
def get_courses() -> List[Course]:
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Course) # SELECT * FROM Course
        return query.all()

# Gets course code given course_id
def get_course_code(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Course.course_code)
                .filter(Course.course_id == course_id)) 
        return query.all()

# Function for editing course code
def edit_course_code(course_id, new_course_code):
    with sqlalchemy.orm.Session(engine) as session:
        course = session.query(Course).filter(Course.course_id == course_id).first()

        if check_unique_code(new_course_code):
            course.course_code = new_course_code
            session.commit()
            return True
        else:
            return False

# Checks if course code is unique
def check_unique_code(course_code):
    with sqlalchemy.orm.Session(engine) as session:
        count = session.query(sqlalchemy.func.count(Course.course_code)).filter(Course.course_code == course_code).scalar()
        return count == 0

#-----------------------------------------------------------------------

# Creates table storing student info
class Student(Base):
    __tablename__ = 'students'
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True) # student net id
    first_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    last_name = sqlalchemy.Column(sqlalchemy.VARCHAR)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# Gets student info and the courses they belong to in alphabetical order by student first name
def get_all_students():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Student.student_id,
                            Student.first_name,
                            Student.last_name,
                            CoursesStudents.course_id)
                .join(CoursesStudents, Student.student_id == CoursesStudents.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), sqlalchemy.asc(Student.last_name))) 
        return query.all()

# Gets student first name based on their netid
def get_student_firstname(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Student.first_name).filter(
            Student.student_id == student_id).one_or_none()

        if query is None:
            return "Default"
        
        return query[0]

#-----------------------------------------------------------------------

# Creates table mapping courses to professors
class CoursesProfs(Base):
    __tablename__ = 'coursesprofs'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    prof_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# Gets all courses that a professor teaches given the prof_id
def get_professor_courses(prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        my_courses = session.query(CoursesProfs).filter(
            CoursesProfs.prof_id == prof_id).all()

        course_data = []
        for course_prof in my_courses:
            course = session.query(Course).filter(
                Course.course_id == course_prof.course_id).first()
            if course:
                course_data.append({
                    'course_id': course.course_id,
                    'course_name': course.course_name
                })

        return course_data

# Function for fetching all professors and the courses they teach
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
                {"net_id": prof.prof_id, 
                "name": f"{prof.first_name} {prof.last_name}", 
                "courses": [prof.course_id]}
                for prof in profs_query.all()
            ]

            superadmins = [
                {"net_id": admin.admin_id, 
                "name": f"{admin.first_name} {admin.last_name}", 
                "courses": [admin.course_id]}
                for admin in admins_query.all()
            ]

            # Combine and return results
            return professors + superadmins

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to fetch data due to: {str(e)}")

# Checks whether a professor teaches a course
def check_prof_in_course(course_id, prof_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Directly check for an existing association record between the professor and the course
        association = session.query(CoursesProfs).filter(
            CoursesProfs.course_id == course_id,
            CoursesProfs.prof_id == prof_id
        ).first()

        # Return True if the association exists, False otherwise
        return association is not None

# Gets courses and professors for each one (FOR ADMIN COURSES PAGE)
def get_courses_and_profs():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, 
                            Professor.first_name, 
                            Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(CoursesProfs.course_id))
        
        results = query.all()
        
        if not results:
            print("No courses fetched from database.")
            return {}

        # Formats query results
        courses = {}

        for course_id, first_name, last_name in results:
            if course_id not in courses:
                courses[course_id] = {'course_id': course_id, 
                                    'professors': []}
            courses[course_id]['professors'].append(f"{first_name} {last_name}")

        print("success")

        return courses

# Gets prof info (FOR ADMIN PROFESSORS PAGE)
def get_prof_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesProfs.course_id, 
                            CoursesProfs.prof_id, 
                            Professor.first_name, 
                            Professor.last_name)
                .join(Professor, CoursesProfs.prof_id == Professor.prof_id)
                .order_by(sqlalchemy.asc(Professor.first_name), sqlalchemy.asc(Professor.last_name)))
        
        results = query.all()
        
        if not results:
            return None

        # Formats query results
        profs = {}

        for course_id, prof_id, first_name, last_name in results:
            if prof_id not in profs:
                profs[prof_id] = {'prof_id': prof_id, 
                                'prof_name': f"{first_name} {last_name}", 
                                'courses': []}
            profs[prof_id]['courses'].append(course_id)

        return profs

#-----------------------------------------------------------------------

# Creates table mapping courses to students
class CoursesStudents(Base):
    __tablename__ = 'coursesstudents'
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR, primary_key=True)

# Gets all courses that a student is in given their student id
def get_student_courses(student_id):
    with sqlalchemy.orm.Session(engine) as session:
        my_courses = session.query(CoursesStudents).filter(
            CoursesStudents.student_id == student_id).all()

        course_data = []
        for student in my_courses:
            course = session.query(Course).filter(
                Course.course_id == student.course_id).first()
            if course:
                course_data.append({
                    'course_id': course.course_id,
                    'course_name': course.course_name
                })

        return course_data

# Checks student enrollment in a course
def check_student_in_course(course_id, student_id):
    with sqlalchemy.orm.Session(engine) as session:
        enrollment = session.query(CoursesStudents).filter(
            CoursesStudents.course_id == course_id,
            CoursesStudents.student_id == student_id
        ).first()

        return enrollment is not None

# Function to enroll a student in a course using the course code
def enroll_student_in_course(student_id, course_code):
    with sqlalchemy.orm.Session(engine) as session:
        # Retrieve the course using the course code
        course = session.query(Course).filter_by(course_code=course_code).first()
        if not course:
            return {"status": "error", "message": "Invalid course code"}

        # Check if the student is already enrolled
        existing_enrollment = session.query(CoursesStudents).filter_by(
            course_id=course.course_id, student_id=student_id).first()
        if existing_enrollment:
            return {"status": "error", "message": "Already enrolled in this course"}

        # Enroll the student in the course
        new_enrollment = CoursesStudents(course_id=course.course_id, 
                                        student_id=student_id)
        session.add(new_enrollment)
        session.commit()

        return {"status": "success", "message": "Course joined successfully"}

# Gets all students enrolled in a course
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
                {"student_id": prof.student_.id,
                "first_name": prof.first_name, 
                "last_name": prof.last_name}
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
                {"student_id": admin.student_id,
                "first_name": admin.first_name,
                "last_name": admin.last_name}
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

# Function for fetching all students and the courses they are enrolled in
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
                CoursesStudents,
                SuperAdmin.admin_id == CoursesStudents.student_id
            ).order_by(SuperAdmin.first_name, SuperAdmin.last_name)

            # Combine all results using union_all
            combined_query = students_query.union_all(professors_query).union_all(superadmins_query)
            results = combined_query.all()

            # Convert results into a list of dictionaries
            merged_results = sorted([
                {
                    "id": result.id,
                    "name": f"{result.first_name} {result.last_name}",
                    "courses": [result.course_id]
                }
                for result in results
            ], key=lambda x: x['course_id'])

            return merged_results

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to fetch data due to: {str(e)}")
        
# Gets student info (FOR ADMIN STUDENTS PAGE)
def get_student_info():
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(CoursesStudents.course_id, 
                            CoursesStudents.student_id, 
                            Student.first_name, 
                            Student.last_name)
                .join(Student, 
                    CoursesStudents.student_id == Student.student_id)
                .order_by(sqlalchemy.asc(Student.first_name), 
                        sqlalchemy.asc(Student.last_name)))
        
        results = query.all()
        
        if not results:
            return None

        # Formats query results
        students = {}

        for course_id, student_id, first_name, last_name in results:
            if student_id not in students:
                students[student_id] = {'student_id': student_id, 
                                        'student_name': f"{first_name} {last_name}", 
                                        'courses': []}
            students[student_id]['courses'].append(course_id)

        return students

#-----------------------------------------------------------------------

# Creates table storing assignment prompts
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
    description = sqlalchemy.Column(sqlalchemy.VARCHAR)

# Gets all assignments for a given course
def get_assignments_for_course(course_id):
    est = pytz.timezone('America/New_York')  # Eastern Standard Time
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
            Prompt.description
        ).filter(Prompt.course_id == course_id).order_by(sqlalchemy.asc(Prompt.deadline)).all()

        current_assignments = []
        past_assignments = []
        for assignment in assignments:
            local_deadline = assignment.deadline.astimezone(est) if assignment.deadline else None
            formatted_deadline = local_deadline.strftime(
                '%m/%d/%Y %I:%M %p %Z') if local_deadline else 'No deadline set'

            assignment_info = {
                'prompt_id': assignment.prompt_id,
                'prompt_title': assignment.prompt_title,
                'prompt_text': assignment.prompt_text,
                'deadline': formatted_deadline,
                'num_turns': assignment.num_turns,
                'created_at': assignment.created_at.astimezone(est).strftime('%Y-%m-%d %H:%M:%S'),
                'description': assignment.description
            }
            if local_deadline is None or local_deadline > now_est:
                current_assignments.append(assignment_info)
            else:
                past_assignments.append(assignment_info)

        return {'current_assignments': current_assignments, 'past_assignments': past_assignments}

# Gets all assignments for a student in a given course
def get_assignments_for_student(student_id, course_id):
    est = pytz.timezone('America/New_York')
    with sqlalchemy.orm.Session(engine) as session:
        now_utc = datetime.now(pytz.utc)  
        now_est = now_utc.astimezone(est)  

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
            Prompt.description,
            completed_subquery  
        ).filter(Prompt.course_id == course_id
        ).order_by(sqlalchemy.asc(Prompt.deadline)).all()
        return categorize_assignments(assignments, now_est)

# Categorize assignments into past and present
def categorize_assignments(assignments, now):
    current_assignments = []
    past_assignments = []
    for a in assignments:
        local_deadline = pytz.utc.localize(a.deadline).astimezone(
            pytz.timezone('America/New_York')) if a.deadline else None

        assignment_tuple = (
            a.prompt_id,
            a.prompt_title,
            local_deadline,
            a.created_at,
            a.description,
            a.completed
        )

        if local_deadline is None or local_deadline > now:
            current_assignments.append(assignment_tuple)
        else:
            past_assignments.append(assignment_tuple)

    return current_assignments, past_assignments

# Gets prompt title by id
def get_prompt_title(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        
        query = (session.query(Prompt.prompt_title).filter(
            Prompt.prompt_id == prompt_id))

        return query.all()

# Gets prompt object by id
def get_prompt_by_id(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        prompt = session.query(Prompt).filter(Prompt.prompt_id == prompt_id).first()
        return prompt

# Gets all current course assignments for a student, with the earliest deadline first (FOR STUDENT ASSIGNMENTS PAGE)
# Marks whether assignment has been completed or not
def get_current_assignments_for_student(student_id, course_id):
    with sqlalchemy.orm.Session(engine) as session:
        
        subquery = (session.query(Conversation.prompt_id)
                    .filter(Conversation.student_id == student_id, 
                            Conversation.prompt_id == Prompt.prompt_id)
                    .exists()).label("completed")

        query = (session.query(Prompt.prompt_id,
                            Prompt.prompt_title,
                            Prompt.deadline,
                            Prompt.past_deadline,
                            Prompt.created_at,
                            subquery)
                 .filter(Prompt.course_id == course_id, 
                        Prompt.past_deadline == False)
                 .order_by(sqlalchemy.asc(Prompt.deadline)))

        results = query.all()
        return results

# Gets assignments for prof (FOR PROF SCORES PAGE)
def get_assignments_for_prof(course_id):
    with sqlalchemy.orm.Session(engine) as session:
        assignments = session.query(
            Prompt.prompt_id,
            Prompt.prompt_title,
        ).filter(Prompt.course_id == course_id
        ).order_by(sqlalchemy.asc(Prompt.deadline)).all()

        return assignments

#-----------------------------------------------------------------------

# Creates table storing practice prompts
class PracticePrompt(Base):
    __tablename__ = 'practiceprompts'
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    course_id = sqlalchemy.Column(sqlalchemy.Integer)
    prof_id = sqlalchemy.Column(sqlalchemy.Integer)
    prompt_text = sqlalchemy.Column(sqlalchemy.Text)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())

# Gets all practice prompts for a given course, ordered by most to least recently created
def get_practice_prompts(course_id) -> List[Prompt]:
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(PracticePrompt.prompt_id, 
                            PracticePrompt.prompt_title, 
                            PracticePrompt.created_at)
                .filter(PracticePrompt.course_id == course_id)
                .order_by(sqlalchemy.desc(PracticePrompt.created_at)))
        
        results = query.all()

        return results

#-----------------------------------------------------------------------

# Creates table storing student conversations with the chatbot
# We only store assignment conversations, not practice ones
class Conversation(Base):
    __tablename__ = 'conversations'
    conv_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    course_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    student_id = sqlalchemy.Column(sqlalchemy.VARCHAR)
    prompt_id = sqlalchemy.Column(sqlalchemy.Integer)
    conv_text = sqlalchemy.Column(sqlalchemy.Text)
    score = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=sqlalchemy.sql.func.now())
    prof_score = sqlalchemy.Column(sqlalchemy.Integer)

# Checks if conv_id is unique
def check_unique_convid(conv_id):
    with sqlalchemy.orm.Session(engine) as session:
        count = session.query(sqlalchemy.func.count(Conversation.conv_id)).filter(
            Conversation.conv_id == conv_id).scalar()
        return count == 0

# Gets the course assignments and their scores for each given a student id
def get_assignments_and_scores_for_student(course_id, student_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(Prompt.prompt_id, 
                            Prompt.prompt_title, 
                            Conversation.conv_id, 
                            Conversation.score)
                 .outerjoin(Conversation, sqlalchemy.and_(
                     Conversation.prompt_id == Prompt.prompt_id, 
                     Conversation.student_id == student_id))
                 .filter(Prompt.course_id == course_id)
                 .order_by(sqlalchemy.asc(Prompt.created_at)))

        results = query.all()
        return results if results else None

# Gets all student scores in alphabetical order for an assignment given the assignment id (FOR PROF SCORES PAGE)
def get_all_scores(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        # Subquery to select students from both Student and SuperAdmin tables
        student_union = session.query(
            Student.student_id.label('student_id'),
            sqlalchemy.func.concat(Student.first_name, ' ', Student.last_name).label('name')
        ).union(
            session.query(
                SuperAdmin.admin_id.label('student_id'),
                sqlalchemy.func.concat(SuperAdmin.first_name, ' ', SuperAdmin.last_name).label('name')
            )
        ).subquery()

        # Main query to get scores
        query = (session.query(
                    student_union.c.name,
                    Conversation.conv_id,
                    Conversation.score,
                    Conversation.prof_score)
                 .join(CoursesStudents, CoursesStudents.student_id == student_union.c.student_id)
                 .join(Prompt, Prompt.course_id == CoursesStudents.course_id)
                 .outerjoin(Conversation, sqlalchemy.and_(
                     Conversation.student_id == student_union.c.student_id,
                     Conversation.prompt_id == Prompt.prompt_id))
                 .filter(Prompt.prompt_id == prompt_id)
                 .order_by(sqlalchemy.asc(student_union.c.name)))

        results = query.all()

        return results

# Gets all scores given prompt_id
def get_scores_for_assignment(prompt_id):
    with sqlalchemy.orm.Session(engine) as session:
        query = (session.query(
                    Conversation.score,
                    Conversation.prof_score)
                 .join(Prompt, Conversation.prompt_id == Prompt.prompt_id)
                 .filter(Prompt.prompt_id == prompt_id)
                 .order_by(sqlalchemy.asc(Prompt.created_at)))

        results = query.all()

        return results

# Gets conversation history given a conv_id
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

# Checks if user exists in students, profs, or superadmin tables
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

# Returns user type or None if not found
def check_user_type(user_id: str):
    if in_students(user_id):
        return "Student"
    if in_profs(user_id):
        return "Professor"
    if in_superadmins(user_id):
        return "SuperAdmin"
    return None 

#-----------------------------------------------------------------------


