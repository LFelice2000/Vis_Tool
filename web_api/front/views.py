from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from core.models import *
from core.views import *
from urllib.parse import unquote, urlparse, parse_qs

import pandas as pd

import ast
import json

notificationServiceThread = None

def is_teacher(value):

    domain = value.split("@")[1]

    if domain == "uam.es":

        return True
    
    return False

def parseUrlParams(url) -> dict:

    parsedUrl = urlparse(unquote(url))
    urlParams = parse_qs(parsedUrl.query)

    urldict = {k: v[0] for k, v in urlParams.items()}

    return urldict

@csrf_exempt
@xframe_options_exempt
def update(request):

    if request.method == "POST":
        
        courseName = request.POST.get("courseName")
        courseShortName = request.POST.get("courseShortName")
        teacher = request.POST.get('username')
        courseId = request.POST.get('courseId')

        dataframe = pd.json_normalize(json.loads(request.POST.get("activities")))
        
        attendanceDataframe = pd.json_normalize(json.loads(request.POST.get("attendance")))
        
        courseStudents = dataframe.filter(regex='First name|Last name|ID number|Email address|Nombre|Apellido\(s\)|Número de ID|Dirección de correo')
        students = getStudentDataframe(courseStudents)

        attendanceInfo = attendanceDataframe[attendanceDataframe.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje'])]
        attendanceSesions = getAttendanceSessionsFromDataframe(attendanceInfo)

        courseContent = dataframe.filter(regex='Quiz|Assignment|Attendance|Cuestionario|Tarea|Asistencia')
        
        quizes, attendance, assignments = getCourseActivitiesFromDataframe(courseContent, attendanceSesions)

        activities = json.dumps({"quiz": quizes,"assignment": assignments, "asistance": attendance})

        studentGradeList = getStudentGradeListFromDataframe(students, dataframe, attendanceInfo, quizes, attendance, assignments)
     
        return redirect(reverse("updateCourse", kwargs={"activities": activities, "courseName": courseName, "courseShortName": courseShortName, "studentGrades": studentGradeList, "teacher": teacher, "courseId": courseId}))

    
@csrf_exempt
@xframe_options_exempt
def teacherPage(request, courseName, courseShortName, teacherMail, courseId):

    context = {
        "courseName": str(courseName),
        "teacherMail": teacherMail,
        "courseId": courseId,
        'courseShortName':courseShortName
    }

    return render(request, "teacherAdmin.html", context=context)

@csrf_exempt
@xframe_options_exempt
def visPage(request):

    if request.method == 'GET':

        url = request.get_full_path()
        urlParams = parseUrlParams(url)

        userMail =  urlParams.get('userMail')
        courseName = urlParams.get('courseFullName')
        courseShortName = urlParams.get('courseName')
        courseId = urlParams.get('CourseId')

        #or userMail == 'luis.felice@estudiante.uam.es'
        if is_teacher(userMail) or userMail == 'luis.felice@estudiante.uam.es':

            if not courseExists(courseName):
            
                context = {
                    'teacherMail': userMail,
                    'courseId': courseId,
                    'courseName': courseName,
                    'courseShortName': courseShortName
                }

                return render(request, 'confObjectives.html', context=context)
            elif userMail in getTeachersInCourse(courseName):

                return redirect(reverse('teacherAdmin', kwargs={"courseName":courseName, 'courseShortName': courseShortName, 'teacherMail': userMail, 'courseId': courseId}))
            
            context = {
                "error": "Error desconocido."
            }
            return render(request, "error.html", context=context)

        currCourse = getCurrCourse(courseName)

        if currCourse:

            #Calculamos el progreso personal
            students = getCourseStudents(courseName)

            if userMail not in getStudentEmails(courseName):

                context = {
                    "error": "El estudiante no esta registrado en la herramienta."
                }

                return render(request, "error.html", context=context)

            personalTotal = []
            globalTotal = []
            for objective in getCourseObjectives(courseName):
                
                
                globalGradeAcum = 0
                for stu in students:
                    
                    personalGradeAcum = 0
                    for activity in getObjectiveActivities(objective.name, currCourse.name):
                        
                        if type(activity) == type(Quiz()):

                            grade = Grade.objects.filter(quiz__id=activity.id, student=stu, course=currCourse).first()

                            if stu.email == userMail:
                                personalGradeAcum += grade.grade * (activity.weight/100)

                            globalGradeAcum += grade.grade * (activity.weight/100)

                        elif type(activity) == type(Assignment()):

                            grade = Grade.objects.filter(assignment__id=activity.id, student=stu, course=currCourse).first()

                            if stu.email == userMail:
                                personalGradeAcum += grade.grade * (activity.weight/100)

                            globalGradeAcum += grade.grade * (activity.weight/100)
                        
                        elif type(activity) == type(Sesion()):
                            
                            
                            at = Attendance.objects.filter(sesions=activity).first()
                            grade = Grade.objects.filter(sesion__id=activity.id, student=stu, course=currCourse).first()
                            
                            if grade and at:
                                if stu.email == userMail:
                                    personalGradeAcum += grade.grade * (at.weight/100)

                                globalGradeAcum += grade.grade * (at.weight/100)

                    if stu.email == userMail:
                        personalResults = {'name': objective.name, 'personalScore': round((personalGradeAcum*10), 2)}
                    
                        personalTotal.append(personalResults)
                    
                globalTotal.append({'objective': objective.name, 'globalScore': round(((globalGradeAcum/students.count())*10), 2)})

            
            for result in personalTotal:
                for globalResult in globalTotal:

                    if result['name'] == globalResult['objective']:

                        result['global'] = globalResult['globalScore']
            

            update = Update.objects.filter(course=currCourse).first()

            context = None

            if update:
                context = {
                    'objectives': personalTotal,
                    'student': userMail,
                    'update': update,
                    'updateBy': update.teacher
                }
            else:
                context = {
                    'objectives': personalTotal,
                    'student': userMail,
                }

            return render(request, "visPage.html", context=context)
        
        context = {
            "error": "La herramienta no esta configurada para este curso"
        }
            
        return render(request, "error.html", context=context)
        
    elif request.method == 'POST':

        objectives = request.POST.getlist("objectives[]")
        courseShortName = request.POST.get('courseShortName')
        userMail = request.POST.get('teacherMail')
        courseId = request.POST.get('courseId')
        courseName = request.POST.get('courseName')
        
        objList = list(dict())
        objList = [{'name': x, 'course':  courseName} for x in objectives]

        context = {
            'objList': str(objList),
            'courseId': courseId,
            'courseName': courseName,
            'courseShortName': courseShortName
        }
        
        return render(request, "confPage.html", context=context)
    
    context = {
        "error": "Error desconocido."
    }

    return render(request, "error.html")

def getStudentDataframe(courseStudents):
    students = list()
    
    for (col, data) in courseStudents.iterrows():
        students.append({"firstName": data.get('Nombre'), "lastName": data.get('Apellido(s)'), "email": data.get('Dirección de correo')})
    
    return students

def getAttendanceSessionsFromDataframe(attendanceInfo):

    attendanceSesions = list()

    for col in attendanceInfo:
        if col != 'Dirección de correo':
            attendanceSesions.append(col.replace(" Todos los estudiantes", ""))
    
    return attendanceSesions

def getCourseActivitiesFromDataframe(courseContent, attendanceSesions):

    quizes = list(dict())
    attendance = list(dict())
    assignments = list(dict())
    i = 0
    j = 0
    k = 0
    for col in courseContent.columns:
        activityType, activityname = col.split(":")
        activityname = activityname.replace(" (Real)", "")
        
        if activityType == "Attendance" or activityType == "Asistencia":
            for session in attendanceSesions:
                attendance.append({"tmpId": j, "type": activityType, "name": activityname, "weight": "", "sesion": session,})
                j += 1
        if activityType == "Quiz" or activityType == "Cuestionario":
            quizes.append({"tmpId": i, "type": activityType, "name": activityname, "weight": ""})

            i += 1
        elif activityType == "Assignment" or activityType == "Tarea":
            assignments.append({"tmpId": k, "type": activityType, "name": activityname, "weight": ""})

            k += 1
    
    return quizes, attendance, assignments

def getStudentGradeListFromDataframe(students, dataframe, attendanceInfo, quizes, attendance, assignments):
    
    i = 0
    studentGradeList = list(dict())
    for student in students:
        studentActivities = dataframe.loc[dataframe['Dirección de correo'] == student['email']].filter(regex='Email address|Quiz|Assignment|Attendance|Dirección de correo|Cuestionario|Tarea|Asistencia')
        studentSessions = attendanceInfo.loc[attendanceInfo['Dirección de correo'] == student['email']]
        studentSessions = studentSessions[studentSessions.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje'])]
        
        activityList = list(dict())
        for quiz in quizes:
            studentGrade = studentActivities[f"{quiz['type']}:{quiz['name']} (Real)"]

            if studentGrade[i] == '-':

                activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': 0})
            
            else:
            
                activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': studentGrade[i]})

        for attend in attendance:

            studentGrade = studentSessions[f"{attend['sesion']} Todos los estudiantes"][i].split(" ")[0]

            if studentGrade == 'P' or studentGrade == 'L' or studentGrade == 'R':

                activityList.append({'type': attend['type'], 'name': attend['name'], 'sesion': attend['sesion'], 'grade': 10})
            
            else:
            
                activityList.append({'type': attend['type'], 'name': attend['name'], 'sesion': attend['sesion'], 'grade': 0})
        
        for assignment in assignments:
            studentGrade = studentActivities[f"{assignment['type']}:{assignment['name']} (Real)"]

            if studentGrade[i] == '-':

                activityList.append({'type': assignment['type'], 'name': assignment['name'], 'grade': 0})
            
            else:
            
                activityList.append({'type': assignment['type'], 'name': assignment['name'], 'grade': float("{:.2f}".format(studentGrade[i]/10))})

        studentGradeList.append({'student': student['email'], 'activities': activityList})
        i += 1

    return studentGradeList

@csrf_exempt
@xframe_options_exempt
def confPage(request):
    
    if request.method == "GET":

        objectiveList = request.GET.get('objList')
        courseName = request.GET.get('courseName')
        courseShortName = request.GET.get('courseShortName')
        teacher = request.GET.get('teacherMail')
        courseId = request.GET.get('courseId')
        updateFlag = request.GET.get('updateFlag')

        if request.GET.get('updateFlag') != None:
            updateFlag = 1

        context = {
            'courseName': courseName,
            'updateFlag': updateFlag,
            'teacher': teacher,
            'courseId': courseId,
            'courseShortName': courseShortName
        }
            
        return render(request, "confPage.html", context=context)
        
    elif request.method == "POST":

        objectiveList = request.POST.get('objList')
        courseName = request.POST.get('courseName')
        courseId = request.POST.get('courseId')
        courseShortName = request.POST.get('courseShortName')

        username = request.POST['username']
        password = request.POST['password']

        dataframe = pd.json_normalize(json.loads(request.POST.get("activities")))
        
        attendanceDataframe = pd.json_normalize(json.loads(request.POST.get("attendance")))

        teacher = Teacher.objects.filter(email=username)
        
        courseStudents = dataframe.filter(regex='First name|Last name|ID number|Email address|Nombre|Apellido\(s\)|Número de ID|Dirección de correo')
        students = getStudentDataframe(courseStudents)

        attendanceInfo = attendanceDataframe[attendanceDataframe.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje'])]
        attendanceSesions = getAttendanceSessionsFromDataframe(attendanceInfo)

        courseContent = dataframe.filter(regex='Quiz|Assignment|Attendance|Cuestionario|Tarea|Asistencia')
        
        quizes, attendance, assignments = getCourseActivitiesFromDataframe(courseContent, attendanceSesions)

        studentGradeList = getStudentGradeListFromDataframe(students, dataframe, attendanceInfo, quizes, attendance, assignments)

        context = {
            'students': students,
            'quizList': quizes,
            'courseName': courseName,
            'teacher': username,
            'studentGrades': studentGradeList,
            'objectiveList': ast.literal_eval(objectiveList),
            'attendanceList': attendance,
            'assignmentList': assignments,
            'courseId': courseId,
            'courseShortName': courseShortName
        }
        
        return render(request, "confActivities.html", context=context)

    context = {
        "error": "Error desconocido."
    }
    return render(request, "error.html", context=context)

@csrf_exempt
@xframe_options_exempt
def confWeigth(request):

    students = request.POST.get("students")
    courseName = request.POST.get("courseName")
    courseShortName = request.POST.get("courseShortName")
    teacher = request.POST.get('teacher')
    studentGrades = request.POST.get("studentGrades")
    objectiveList = request.POST.get("objectiveList")
    activitiesInfo = request.POST.get("activitiesInfo")
    courseId = request.POST.get('courseId')


    return redirect(reverse("createCourse", kwargs={'activities': activitiesInfo, 'studentList': students, "courseName": courseName, 'courseShortName': courseShortName, 'teacher': teacher, 'studentGrades': studentGrades, 'objectiveList': objectiveList, 'courseId': courseId}))

@xframe_options_exempt
def error(request, error):

    context = {
        "error": error
    }

    return render(request, "error.html", context=context)

@csrf_exempt
@xframe_options_exempt
def addTeacher(request, courseName, courseShortName, teacherMail,courseId):

    if request.method == 'POST':

        
    context = {
        'courseName': courseName,
        'courseShortName': courseShortName,
        'teacherMail': teacherMail,
        'courseId': courseId
    }

    return render(request, "addTeacher.html", context=context)