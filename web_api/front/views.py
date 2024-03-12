from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from core.models import *
from core.utils import *
from urllib.parse import unquote, urlparse, parse_qs
from django.http import JsonResponse
from datetime import datetime

import pandas as pd
import re

import ast
import json

notificationServiceThread = None

def is_teacher(value):


    if value:
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
        group = request.POST.get('group')

        dataframe = pd.json_normalize(json.loads(request.POST.get("activities")))
        
        attendanceDataframe = pd.json_normalize(json.loads(request.POST.get("attendance")))
        
        courseStudents = dataframe.filter(regex='First name|Last name|ID number|Email address|Nombre|Apellido\(s\)|Número de ID|Dirección de correo')
        students = getStudentDataframe(courseStudents)

        attendanceInfo = attendanceDataframe[attendanceDataframe.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje', 'Grupos'])]
        attendanceSesions = getAttendanceSessionsFromDataframe(attendanceInfo)

        courseContent = dataframe.filter(regex='Quiz|Assignment|Attendance|Cuestionario|Tarea|Asistencia')
        
        quizes, attendance, assignments, repeatedActivities = getCourseActivitiesFromDataframe(courseContent, attendanceSesions, group)

        activities = json.dumps({"quiz": quizes,"assignment": assignments, "asistance": attendance})

        studentGradeList = getStudentGradeListFromDataframe(students, dataframe, attendanceInfo, quizes, attendance, assignments)

        res = updateCourse(activities, courseName, courseShortName, studentGradeList, teacher, courseId, group)
        if res['status'] == "error":
            return redirect(reverse("error", kwargs={"error": res['error']}))
        
        return redirect(reverse("teacherAdmin", kwargs={"courseName":courseName, "courseShortName": courseShortName, "teacherMail":teacher, 'courseId': courseId}))


    
@csrf_exempt
@xframe_options_exempt
def teacherPage(request, courseName, courseShortName, teacherMail, courseId):

    currCourse = getCurrCourse(courseName)

    globalTotal = []
    for objective in getCourseObjectives(courseName):

        gloScores = getGlobalScore(objective)
        globalTotal.append({'name': gloScores.objective.name, 'globalScore': gloScores.percentage})

    context = {
        "courseName": str(courseName),
        "teacherMail": teacherMail,
        "courseId": courseId,
        'courseShortName':courseShortName,
        'globalObjectives': globalTotal
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
        if is_teacher(userMail):

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
            student = getStudent(userMail)
            
            if userMail not in getStudentEmails(courseName):

                context = {
                    "error": "El estudiante no esta registrado en la herramienta."
                }

                return render(request, "error.html", context=context)

            personalTotal = []

            for objective in getCourseObjectives(courseName):
                
                globalScore = getGlobalScore(objective)
                personalScore = getPersonalScores(objective, student)
                    
                personalTotal.append({'name': objective.name, 'globalScore': float(globalScore.percentage), 'personalScore': float(personalScore.percentage)})

            update = Update.objects.filter(course=currCourse).first()
            studentName = Student.objects.filter(email=userMail).first().name

            context = None

            if update:
                context = {
                    'objectives': personalTotal,
                    'objectivesJson': json.dumps(personalTotal),
                    'student': studentName,
                    'update': update,
                    'updateBy': update.teacher
                }
            else:
                context = {
                    'objectivesJson': json.dumps(personalTotal),
                    'objectives': personalTotal,
                    'student': studentName,
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

    attendanceSesions = set()

    for col in attendanceInfo:
        if col != 'Dirección de correo':
            attendanceSesions.add(re.sub(r'\.\d+$', '', col.replace(" Todos los estudiantes", "")))
    
    return list(attendanceSesions)

def getCourseActivitiesFromDataframe(courseContent, attendanceSesions, group):

    quizes = list(dict())
    attendance = list(dict())
    assignments = list(dict())
    repeatedActivities = list()
    i = 0
    j = 0
    k = 0
    for col in courseContent.columns:
        activityType, activityname = col.split(":")
        activityname = re.sub(r'\.\d+$', '', activityname.replace(" (Real)", ""))
        actGroup = re.findall(r'\((.*?)\)', activityname)

        if len(actGroup) == 0 or ('NE' not in actGroup[0] and actGroup[0].replace('grupo ', '') == group):
            
        
            if activityType == "Quiz" or activityType == "Cuestionario":
                
                if any(d["name"] == activityname for d in quizes):
                    repeatedActivities.append(activityname)

                else:
                    quizes.append({"tmpId": i, "type": activityType, "name": activityname, "weight": ""})

                i += 1
            elif activityType == "Assignment" or activityType == "Tarea":

                if any(d["name"] == activityname for d in assignments):
                    repeatedActivities.append(activityname)
                
                assignments.append({"tmpId": k, "type": activityType, "name": activityname, "weight": ""})

                k += 1

    for session in attendanceSesions:

        attendance.append({"tmpId": j, "type": 'Asistencia', "weight": "", "sesion": session})
        j += 1
    
    list(map(lambda x: x["sesion"], attendance))
    return quizes, attendance, assignments, repeatedActivities

def getStudentGradeListFromDataframe(students, dataframe, attendanceInfo, quizes, attendance, assignments):
    
    i = 0
    studentGradeList = list(dict())
    for student in students:
        studentActivities = None
        studentSessions = None

        try:
            studentActivities = dataframe.loc[dataframe['Dirección de correo'] == student['email']].filter(regex='Email address|Quiz|Assignment|Attendance|Dirección de correo|Cuestionario|Tarea|Asistencia')
        except:
            pass
        
        try:
            studentSessions = attendanceInfo.loc[attendanceInfo['Dirección de correo'] == student['email']]
            studentSessions = studentSessions[studentSessions.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje', 'Grupos'])]
        except:
            pass
        
        activityList = list(dict())

        if len(studentActivities):
        
            for quiz in quizes:
                studentGrade = studentActivities[f"{quiz['type']}:{quiz['name']} (Real)"]

                if studentGrade[i] == '-':

                    activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': 0})
                
                else:
                
                    activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': studentGrade[i]})
            
            for assignment in assignments:
                studentGrade = studentActivities[f"{assignment['type']}:{assignment['name']} (Real)"]

                if studentGrade[i] == '-':

                    activityList.append({'type': assignment['type'], 'name': assignment['name'], 'grade': 0})
                
                else:
                
                    activityList.append({'type': assignment['type'], 'name': assignment['name'], 'grade': studentGrade[i]})
        
        if len(studentSessions):
            for attend in attendance:
                
                studentGrade = None
                if re.match(r'.+?\s\d+$', attend['sesion']):
                    
                    try:
                        studentGrade = studentSessions[f"{attend['sesion']}"][i]
                    except Exception as e:
                        print(f"Student sesion: {studentSessions}\nattend: {attend}")

                else:
                    studentGrade = studentSessions[f"{attend['sesion']} Todos los estudiantes"][i]

                if studentGrade:

                    studentGrade = studentGrade.split(" ")[0]

                    if studentGrade == 'P' or studentGrade == 'L' or studentGrade == 'R':

                        activityList.append({'type': attend['type'], 'sesion': attend['sesion'], 'grade': 10})
                    
                    else:
                    
                        activityList.append({'type': attend['type'], 'sesion': attend['sesion'], 'grade': 0})

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
        group = request.POST.get('group')
        students = request.POST.get('students')
        
        username = request.POST['username']
        password = request.POST['password']

        dataframe = pd.json_normalize(json.loads(request.POST.get("activities")))
        attendanceDataframe = pd.json_normalize(json.loads(request.POST.get("attendance")))
        studentsDataframe = pd.json_normalize(json.loads(request.POST.get('students'))).dropna(subset=['Grupos'])

        teacher = Teacher.objects.filter(email=username)
        
        courseStudents = studentsDataframe[studentsDataframe['Grupos'].str.contains(group)].filter(regex="Nombre|Apellido\(s\)|Dirección de correo")
        students = getStudentDataframe(courseStudents)

        attendanceInfo = attendanceDataframe[attendanceDataframe.columns.difference(['Apellido(s)', 'Nombre', 'ID de estudiante', 'P', 'L', 'E', 'A', 'R','J','I', 'Sesiones tomadas', 'Puntuación', 'Porcentaje', 'Grupos'])]
        attendanceSesions = getAttendanceSessionsFromDataframe(attendanceInfo)

        courseContent = dataframe.filter(regex='Quiz|Assignment|Attendance|Cuestionario|Tarea|Asistencia')
        
        quizes, attendance, assignments, repeatedActivities = getCourseActivitiesFromDataframe(courseContent, attendanceSesions, group)

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
            'courseShortName': courseShortName,
            'group': group
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
    group = request.POST.get('group')

    res = createCourse(activitiesInfo, students, courseName, courseShortName, teacher, studentGrades, objectiveList, courseId, group)

    if res['status'] == "error":
        return redirect(reverse("error", kwargs={"error": res['error']}))

    return redirect(reverse("teacherAdmin", kwargs={"courseName":courseName, 'courseShortName':courseShortName, "teacherMail":teacher, 'courseId': courseId}))

@xframe_options_exempt
def error(request, error):

    context = {
        "error": error
    }

    return render(request, "error.html", context=context)

@csrf_exempt
@xframe_options_exempt
def manageStudent(request, courseName, courseShortName, teacherMail,courseId):

    students = getStudentEmails(courseName)

    context = {
        'courseName': courseName,
        'courseShortName': courseShortName,
        'teacherMail': teacherMail,
        'courseId': courseId,
        'students': students
    }

    return render(request, "manageStudents.html", context=context)

@csrf_exempt
@xframe_options_exempt
def manageTeacher(request, courseName, courseShortName, teacherMail,courseId):

    teachers = getTeachersInCourse(courseName)

    context = {
        'courseName': courseName,
        'courseShortName': courseShortName,
        'teacherMail': teacherMail,
        'courseId': courseId,
        'teachers': teachers
    }

    return render(request, "manageTeachers.html", context=context)

@csrf_exempt
@xframe_options_exempt
def addTeacher(request, courseName, courseShortName, teacherMail,courseId):


    if request.method == 'POST':

        teachers = request.POST.getlist("objectives[]")

        for teacher in teachers:

            if not teacherExists(teacher):

                createTeacher(teacher, courseName)
            else:
                addTeacherToCourse(courseName, teacher)

        return redirect(reverse("manageTeacher", kwargs={'courseName': courseName, 'courseShortName': courseShortName, 'teacherMail': teacherMail, 'courseId': courseId}))
    
    context = {
        'courseName': courseName,
        'courseShortName': courseShortName,
        'teacherMail': teacherMail,
        'courseId': courseId
    }

    return render(request, "addTeacher.html", context=context)

@csrf_exempt
@xframe_options_exempt
def removeTeacher(request, courseName, courseShortName, teacherMail,courseId):

    if request.method == 'POST':

        teacher = request.POST.get("teacherToDelete")

        if not deleteTeacher(teacher, courseName):
            print('error')

        return redirect(reverse("manageTeacher", kwargs={'courseName': courseName, 'courseShortName': courseShortName, 'teacherMail': teacherMail, 'courseId': courseId}))
    
@csrf_exempt
@xframe_options_exempt
def removeStudent(request, courseName, courseShortName, teacherMail,courseId):

    if request.method == 'POST':

        student = request.POST.get("studentToDelete")

        print(student)
        if not deleteStudent(student, courseName):
            print('error')

        return redirect(reverse("manageTeacher", kwargs={'courseName': courseName, 'courseShortName': courseShortName, 'teacherMail': teacherMail, 'courseId': courseId}))

@csrf_exempt
@xframe_options_exempt
def addStudent(request, courseName, courseShortName, teacherMail,courseId):


    if request.method == 'POST':

        students = request.POST.getlist("objectives[]")

        for student in students:

            addStudentToCourse(json.loads(student), courseName)

        return redirect(reverse("teacherAdmin", kwargs={'courseName': courseName, 'courseShortName': courseShortName, 'teacherMail': teacherMail, 'courseId': courseId}))
    
    context = {
        'courseName': courseName,
        'courseShortName': courseShortName,
        'teacherMail': teacherMail,
        'courseId': courseId
    }

    return render(request, "addStudent.html", context=context)

@csrf_exempt
@xframe_options_exempt
def studentInfo(request, courseName, courseShortName, teacherMail,courseId):

    studentMail = request.POST.get('studentMail')

    currCourse = getCurrCourse(courseName)
    student = getStudent(studentMail)

    if studentMail not in getStudentEmails(courseName) or not student:

        JsonResponse({'state': 'error'})

    personalTotal = []
    for objective in getCourseObjectives(currCourse.name):

        stuScores = getPersonalScores(objective, student)
        
        if stuScores:
            personalResults = {'name': objective.name, 'personalScore': float(stuScores.percentage)}

            personalTotal.append(personalResults)

    return JsonResponse({'state': 'succeess', 'objectives': json.dumps(personalTotal)})