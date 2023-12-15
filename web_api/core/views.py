from django.shortcuts import render, redirect
from django.urls import reverse
import ast
from django.http import HttpResponseNotFound
from core.models import Course, Sesion, Student, Quiz, Teacher, Grade, Objective, Assignment, Attendance
import os


def createCourse(request, activities, studentList, courseName, teacher, studentGrades, objectiveList):
    
    activitiesObj = ast.literal_eval(activities)
    studentsObj = ast.literal_eval(studentList)
    studentGradesObj = ast.literal_eval(studentGrades)
    objectiveListObj = ast.literal_eval(objectiveList)

    teacher = Teacher(email=teacher)
    teacher.save()

    course = Course(name=courseName)
    course.save()

    for objective in objectiveListObj:

        obj = Objective(name=objective['name'], course=course)
        obj.save()

    for student in studentsObj:

        stndt = Student(email=student['email'], name=f"{student['firstName']} {student['lastName']}")
        stndt.save()

        course.students.add(stndt)

    for activity in activitiesObj['quiz']:

        obj = Objective.objects.filter(name=activity['objective'])

        act = Quiz(name=activity['activityName'], weight=float(activity['weigth']), objective=obj[0], course=course)
        act.save()
    
    for activity in activitiesObj['assignment']:

        obj = Objective.objects.filter(name=activity['objective'])

        act = Assignment(name=activity['activityName'], weight=float(activity['weigth']), objective=obj[0], course=course)
        act.save()
    
    
    for activity in activitiesObj['asistance']:

        ses = Sesion(name=activity['sesion'])
        ses.save()

        obj = Objective.objects.filter(name=activity['objective'])

        act = Attendance(name=activity['activityName'], course=course, objective=obj[0], weight=float(activity['weigth']))
        act.save()

        act.sesions.add(ses)

    
    for student in studentGradesObj:

        stu = Student.objects.filter(email=student['student']).first()

        if stu:
            for activity in student['activities']:

                if activity['type'] == 'Cuestionario':

                    act = Quiz.objects.filter(name=activity['name']).first()
                    
                    if act:
                        grade = Grade(grade=activity['grade'])
                        grade.save()

                        grade.student.add(stu)
                        grade.course.add(course)

                        act.grade.add(grade)
                        act.save()
                    
                elif activity['type'] == 'Tarea':

                    act = Assignment.objects.filter(name=activity['name']).first()
                    
                    if act:
                        grade = grade = Grade(grade=activity['grade'])
                        grade.save()

                        grade.student.add(stu)
                        grade.course.add(course)

                        act.grade.add(grade)
                        act.save()

                elif activity['type'] == 'Asistencia':
                    act = Attendance.objects.filter(name=activity['name']).first()
                    
                    attendanceAssigned = False
                    for attendanceAct in activitiesObj['asistance']:
                        if attendanceAct['sesion'] == activity['sesion']:
                            attendanceAssigned = True

                    if act and attendanceAssigned:
                        
                        grade = Grade(grade=activity['grade'])
                        grade.save()

                        grade.student.add(stu)
                        grade.course.add(course)

                        act.grade.add(grade)
                        act.save()

    return redirect(reverse("teacherAdmin"))

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

        return course.students.all()
    
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
        studentQuizes = Attendance.objects.filter(grade__student=student, course=course)

        grades = []
        for quiz in studentQuizes:
            
            grades.append((quiz.grade.first(), quiz.weight))

        return grades

    return None

def getStudentEmails(courseName):

    students = getCourseStudents(courseName)

    if students:
        emails = []
        for student in students:
            emails.append(student.email)
        
        return emails
    
    return None


def courseExists(courseName):

    return Course.objects.filter(name=courseName).exists()