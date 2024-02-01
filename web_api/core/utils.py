import ast
import json

from core.models import Course, Sesion, Student, Quiz, Teacher, Grade, Objective, Assignment, Attendance, Update

from django.db import IntegrityError
from django.db import transaction

def createCourse(activities, studentList, courseName, courseShortName, teacher, studentGrades, objectiveList, courseId):
    
    activitiesObj = ast.literal_eval(activities)
    studentsObj = ast.literal_eval(studentList)
    studentGradesObj = ast.literal_eval(studentGrades)
    objectiveListObj = ast.literal_eval(objectiveList)
    
    try:
        with transaction.atomic():
            course = Course(name=courseName)
            course.save()

            dbteacher = Teacher.objects.filter(email=teacher, course=course)

            if dbteacher.count() < 1:
                dbteacher = Teacher(email=teacher)
                dbteacher.save()

                dbteacher.course.add(course)

            for objective in objectiveListObj:

                if  Objective.objects.filter(name=objective['name'], course=course).count() > 0:
                    raise IntegrityError
                
                obj = Objective(name=objective['name'], course=course)
                obj.save()

            for student in studentsObj:

                stndt = None
                if student['email'] not in getRegisteredStudents():
                    stndt = Student(email=student['email'], name=f"{student['firstName']} {student['lastName']}")
                    stndt.save()
                else:
                    stndt = Student.objects.filter(email=student['email']).first()

                stndt.course.add(course)

            for activity in activitiesObj['quiz']:

                obj = Objective.objects.filter(name=activity['objective'], course=course)
                
                act = Quiz(name=activity['activityName'], weight=float(activity['weigth']), objective=obj[0], course=course)
                act.save()

            for activity in activitiesObj['assignment']:

                obj = Objective.objects.filter(name=activity['objective'], course=course)

                if obj:
                    act = Assignment(name=activity['activityName'], weight=float(activity['weigth']), objective=obj[0], course=course)
                    act.save()

            for activity in activitiesObj['asistance']:

                act = Attendance(name=activity['activityName'], course=course, weight=float(activity['weigth']))
                act.save()
                
            for student in studentGradesObj:

                stu = Student.objects.filter(email=student['student'], course=course).first()

                if stu:
                    for activity in student['activities']:

                        if activity['type'] == 'Cuestionario':

                            act = Quiz.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                grade = Grade(grade=activity['grade'])
                                grade.save()

                                grade.student.add(stu)
                                grade.course.add(course)

                                act.grade.add(grade)
                                act.save()
                            
                        elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                grade = Grade(grade=activity['grade'])
                                grade.save()

                                grade.student.add(stu)
                                grade.course.add(course)

                                act.grade.add(grade)
                                act.save()

                        elif activity['type'] == 'Asistencia':
                            
                            act = Attendance.objects.filter(name=activity['name'], course=course).first()

                            for attendanceAct in activitiesObj['asistance']:

                                attendanceAssigned = False
                                
                                objectiveName = ""
                                if attendanceAct['sesion'] == activity['sesion']:
                                    attendanceAssigned = True
                                    objectiveName = attendanceAct['objective']

                                if act and attendanceAssigned:
                                    
                                    grade = Grade(grade=activity['grade'])
                                    grade.save()

                                    grade.student.add(stu)
                                    grade.course.add(course)

                                    obj = Objective.objects.filter(name=objectiveName, course=course).first()

                                    ses = Sesion.objects.filter(name=activity['sesion'], objective=obj).first()
                                    if not ses:

                                        ses = Sesion(name=activity['sesion'], objective=obj)
                                        ses.save()


                                    ses.grade.add(grade)

                                    act.sesions.add(ses)
                                    act.save()
    except Exception as e:
        
        return {"status": "error", "error": f"Error creating the course ({e})"}

    return {"status": "success"}

def updateCourse(activities, courseName, courseShortName, studentGrades, teacher, courseId):
    
    activitiesObj = json.loads(activities)
    studentGradesObj = json.loads(studentGrades)
    
    try:
        with transaction.atomic():
            
            course = Course.objects.filter(name=courseName).first()
                
            for student in studentGradesObj:

                stu = Student.objects.filter(email=student['student'], course=course).first()

                if stu:
                    for activity in student['activities']:

                        if activity['type'] == 'Cuestionario':

                            act = Quiz.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(quiz__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    Grade.objects.filter(id=grade.id).update(grade=float(activity['grade']))

                        elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(assignment__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    Grade.objects.filter(id=grade.id).update(grade=float(activity['grade']))
                        
                        elif activity['type'] == 'Asistencia':
                            
                            act = Attendance.objects.filter(name=activity['name'], course=course).first()
                            
                            for attendanceAct in activitiesObj['asistance']:
                                attendanceAssigned = False
                                
                                if attendanceAct['sesion'] in getAttendaceSessions(courseName):
                                    attendanceAssigned = True

                                if act and attendanceAssigned:
                                    
                                    for sesion in act.sesions.all():

                                        if sesion.name == activity['sesion']:
                                            
                                            grade = Grade.objects.filter(sesion__id=sesion.id, student__id=stu.id).first()

                                            if grade and grade.grade != activity['grade']:
                                                Grade.objects.filter(id=grade.id).update(grade=float(activity['grade']))

            oldUpdate = Update.objects.filter(course=course).first()
            if oldUpdate:

                oldUpdate.delete()

            t = Teacher.objects.filter(email=teacher).first()
            newUpdate = Update(course=course, teacher=t)
            newUpdate.save()
             
    except Exception as e:
        print(e)
        return {"status": "error", "error": f"Error creating the course ({e})"}

    return {"status": "success"}

def getCourseObjectives(courseName):

    course = Course.objects.filter(name=courseName).first()
    if not course:
        return None

    return Objective.objects.filter(course=course)

def getTeacher(email):

    return Teacher.objects.filter(email=email).first()

def getCurrCourse(courseName):

    return Course.objects.filter(name=courseName).first()

def getCourseStudents(courseName):

    course = Course.objects.filter(name=courseName).first()

    if course:
        students = Student.objects.filter(course=course).all()

        if students:

            return students
    
    return None

def getStudentQuizGrades(courseName, studentMail):
    
    course = Course.objects.filter(name=courseName).first()

    if course:

        student = Student.objects.get(email=studentMail)
        studentQuizes = Quiz.objects.filter(grade__student=student, course=course)

        grades = []
        for quiz in studentQuizes:
            
            grades.append((quiz.grade.first(), quiz.weight))

        return grades

    return None

def getStudentAssignmentGrades(courseName, studentMail):

    course = Course.objects.filter(name=courseName).first()

    if course:

        student = Student.objects.get(email=studentMail)
        studentQuizes = Assignment.objects.filter(grade__student=student, course=course)

        grades = []
        for quiz in studentQuizes:
            
            grades.append((quiz.grade.first(), quiz.weight))

        return grades

    return None

def getStudentAttendanceGrades(courseName, studentMail):

    course = Course.objects.filter(name=courseName).first()

    if course:

        student = Student.objects.get(email=studentMail)
        attendance = Attendance.objects.filter(course=course).first()

        if attendance:
            grades = []
            
            for ses in attendance.sesions.all():

                ses_grade = Grade.objects.filter(sesion__id=ses.id, student__id=student.id).first()

                if ses_grade:
            
                    grades.append((ses_grade, attendance.weight))

            return grades

    return None

def getStudentEmails(courseName):

    students = getCourseStudents(courseName)

    if students:
        emails = [s.email for s in students]
        return emails
    
    return None


def courseExists(courseName):

    return Course.objects.filter(name=courseName).exists()

def getTeachersInCourse(courseName):

    if courseExists(courseName):

        course = Course.objects.filter(name=courseName).first()
        courseTeachers = []
        for teacher in Teacher.objects.filter(course=course):

            courseTeachers.append(teacher.email)
        
        return courseTeachers
    
    return None

def getRegisteredStudents():

    return [s.email for s in Student.objects.all()]

def getAttendaceSessions(courseName):

    cour = Course.objects.filter(name=courseName).first()

    if cour:
        at = Attendance.objects.filter(course=cour).first()

        if at:
            ses = at.sesions.all()

            if ses:

                return [s.name for s in ses]

    return None

def getObjectiveActivities(objectiveName, Coursename):

    objectivesACtivities = []
    course = Course.objects.filter(name=Coursename).first()

    if course:

        obj = Objective.objects.filter(course=course, name=objectiveName).first()
        quizes = Quiz.objects.filter(objective=obj, course=course)

        objectivesACtivities += [q for q in quizes]

        assignment = Assignment.objects.filter(objective=obj, course=course)
        objectivesACtivities += [q for q in assignment]
        
        attendance = Attendance.objects.filter(course=course).first()

        if attendance:
            sesions = Sesion.objects.filter(objective=obj, attendance=attendance)
            objectivesACtivities += [q for q in sesions]

        return objectivesACtivities
    
    return None

def getCourseTeacherEmails(courseName):

    course = Course.objects.filter(name=courseName).first()
    
    if course:

        return [t.email for t in Teacher.objects.filter(course=course)]
    
    return None

def createTeacher(email, courseName):

    course = Course.objects.filter(name=courseName).first()

    if course:
        try:
            with transaction.atomic():
                
                teacher = Teacher(email=email)
                teacher.save()

                teacher.course.add(course)

        except Exception as e:
            
            return None
    
    return None

def teacherExists(email):

    return Teacher.objects.filter(email=email).first()

def addTeacherToCourse(courseName, email):

    course = Course.objects.filter(name=courseName).first()

    if course:
        try:
            with transaction.atomic():
                
                teacher = Teacher.objects.filter(email=email).first()

                teacher.course.add(course)

        except Exception as e:
            
            return None
    
    return None