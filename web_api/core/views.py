from django.shortcuts import render, redirect
from django.urls import reverse
import ast
from core.models import Course, Sesion, Student, Quiz, Teacher, Grade, Objective, Assignment, Attendance

from django.db import IntegrityError
from django.db import transaction

def createCourse(request, activities, studentList, courseName, courseShortName, teacher, studentGrades, objectiveList, courseId):
    
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

                obj = Objective.objects.filter(name=activity['objective'], course=course)

                act = Attendance(name=activity['activityName'], course=course, objective=obj[0], weight=float(activity['weigth']))
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

                            attendanceAssigned = False
                            for attendanceAct in activitiesObj['asistance']:
                                if attendanceAct['sesion'] == activity['sesion']:
                                    attendanceAssigned = True

                            if act and attendanceAssigned:
                                
                                grade = Grade(grade=activity['grade'])
                                grade.save()

                                grade.student.add(stu)
                                grade.course.add(course)

                                ses = Sesion(name=activity['sesion'])
                                ses.save()

                                ses.grade.add(grade)

                                act.sesions.add(ses)
                                act.save()
    except Exception as e:
        print(e)
        print("Error creating course")
        return redirect(reverse("error"))

    return redirect(reverse("teacherAdmin", kwargs={"courseName":courseName, 'courseShortName':courseShortName, "teacherMail":teacher, 'courseId': courseId}))

def updateCourse(request, activities, courseName, courseShortName, studentGrades, teacher, courseId):
    
    activitiesObj = ast.literal_eval(activities)
    studentGradesObj = ast.literal_eval(studentGrades)
    
    try:
        with transaction.atomic():
            
            course = Course.objects.filter(name=courseName).first()
            dbteacher = Teacher.objects.filter(email=teacher, course=course)
                
            for student in studentGradesObj:

                stu = Student.objects.filter(email=student['student'], course=course).first()

                if stu:
                    for activity in student['activities']:

                        if activity['type'] == 'Cuestionario':

                            act = Quiz.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(quiz__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    print(Grade.objects.filter(id=grade.id).update(grade=float(activity['grade'])))

                        elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(assignment__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    print(Grade.objects.filter(id=grade.id).update(grade=float(activity['grade'])))
                        
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
                                                print(Grade.objects.filter(id=grade.id).update(grade=float(activity['grade'])))
                        """
                         elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(assignment__id=act.id).first()

                                if grade and grade.grade != activity['grade']:
                                    grade.grade = float(activity['grade'])
                                    grade.save()

                        elif activity['type'] == 'Asistencia':
                            
                            act = Attendance.objects.filter(name=activity['name'], course=course).first()
                            
                            attendanceAssigned = False
                            for attendanceAct in activitiesObj['asistance']:
                                if attendanceAct['sesion'] in getAttendaceSessions(courseName):
                                    attendanceAssigned = True

                                if act and attendanceAssigned:

                                    grade = Grade.objects.filter(attendance__id=act.id).first()

                                    if grade and grade.grade != activity['grade']:
                                        grade.grade = float(activity['grade'])
                                        grade.save()
                        """
                       
    except Exception as e:
        print(e)
        return redirect(reverse("error"))

    return redirect(reverse("teacherAdmin", kwargs={"courseName":courseName, "courseShortName": courseShortName, "teacherMail":teacher, 'courseId': courseId}))

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