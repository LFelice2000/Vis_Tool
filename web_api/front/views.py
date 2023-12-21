from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from core.models import *
from core.views import *

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

    parsedUrl = url.replace("%40", "@").replace("?", '').replace('/','')
    urlParams = parsedUrl.split('&')

    urldict = dict()
    for param in urlParams:
        key, value = param.split('=')
        urldict.update({key: value})

    return urldict

def update(request):
    return render(request, "testTemplate.html")

@csrf_exempt
@xframe_options_exempt
def teacherPage(request):

    return render(request, "teacherAdmin.html")

@csrf_exempt
@xframe_options_exempt
def visPage(request):

    if request.method == 'GET':

        url = request.get_full_path()
        urlParams = parseUrlParams(url)

        userMail =  urlParams.get('userMail')
        courseName = urlParams.get('courseName')
        courseId = urlParams.get('CourseId')
        language = urlParams.get('lan')
        
        #or userMail == 'luis.felice@estudiante.uam.es'
        if is_teacher(userMail) or userMail == 'luis.felice@estudiante.uam.es':

            if not getTeacher(userMail) or (getTeacher(userMail) and not courseExists(courseName)):
            
                context = {
                    'teacherMail': userMail,
                    'courseId': courseId,
                    'courseName': courseName
                }

                return render(request, 'confObjectives.html', context=context)
            
            return redirect(reverse('teacherAdmin'))

        currCourse = getCurrCourse(courseName)

        if currCourse:

            #Calculamos el progreso personal
            students = getCourseStudents(courseName)

            if userMail not in getStudentEmails(courseName):
                return render(request, "error.html")

            percentageObjectives = list(dict())
            for objective in getCourseObjectives(courseName):

                #Variables para el progreso personal
                gradeAcumulator = 0
                weigthAcumulator = 0
                personalPercentage = 0
                
                #Variables para el progreso global
                globalGrade = 0
                globalWeigth = 0
                globalPercentage = 0

                for student in students:
                    
                    for (grade, weigth) in getStudentQuizGrades(courseName, student.email):
                        
                        currStudent = ""
                        if grade:
                            if student.email == userMail:
                                
                                currStudent = f"{student.email}"
                                gradeAcumulator += (float(grade.grade) * (float(weigth)/100))
                                weigthAcumulator += float(weigth)/100

                                personalPercentage = (gradeAcumulator / (10*weigthAcumulator))*100

                            globalGrade += (float(grade.grade) * (float(weigth)/100))
                            globalWeigth += float(weigth)/100

                            globalPercentage = (globalGrade / (10*globalWeigth))*100
                    
                    for (grade, weigth) in getStudentAssignmentGrades(courseName, student.email):

                        if grade:
                            if student.email == userMail:
                                
                                currStudent = f"{student.email}"
                                gradeAcumulator += (float(grade.grade) * (float(weigth)/100))
                                weigthAcumulator += float(weigth)/100

                                personalPercentage = (gradeAcumulator / (10*weigthAcumulator))*100

                            globalGrade += (float(grade.grade) * (float(weigth)/100))
                            globalWeigth += float(weigth)/100

                            globalPercentage = (globalGrade / (10*globalWeigth))*100
                    
                    for (grade, weigth) in getStudentAttendanceGrades(courseName, student.email):

                        if grade:
                            if student.email == userMail:
                                
                                currStudent = f"{student.email}"
                                gradeAcumulator += (float(grade.grade) * (float(weigth)/100))
                                weigthAcumulator += float(weigth)/100

                                personalPercentage = (gradeAcumulator / (10*weigthAcumulator))*100

                            globalGrade += (float(grade.grade) * (float(weigth)/100))
                            globalWeigth += float(weigth)/100

                            globalPercentage = (globalGrade / (10*globalWeigth))*100


                percentageObjectives.append({"objective": objective.name, "percentage": round(personalPercentage, 2), "global": round(globalPercentage, 2)})

            context = {
                'activities': percentageObjectives,
                'student': currStudent
            }

            return render(request, "visPage.html", context=context)
        
    elif request.method == 'POST':

        objectives = request.POST.getlist("objectives[]")
        userMail = request.POST.get('teacherMail')
        courseId = request.POST.get('courseId')
        courseName = request.POST.get('courseName')
        
        objList = list(dict())
        objList = [{'name': x, 'course':  courseName} for x in objectives]

        context = {
            'objList': str(objList),
            'courseId': courseId,
            'courseName': courseName
        }
        
        return render(request, "confPage.html", context=context)
        
    return render(request, "error.html")

@csrf_exempt
@xframe_options_exempt
def confPage(request):
    
    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        courseId = request.POST.get('courseId')
        objectiveList = request.POST.get('objList')
        courseName = request.POST.get('courseName')

        print(f"JSON: {json.loads(request.POST.get('activities'))}")

        dataframe = pd.json_normalize(json.loads(request.POST.get("activities")))
        print(dataframe)
        
        attendanceDataframe = pd.json_normalize(json.loads(request.POST.get("attendance")))

        teacher = Teacher.objects.filter(email=username)
        
        if teacher.count() == 0:

            students = list()
            courseStudents = dataframe.filter(regex='First name|Last name|ID number|Email address|Nombre|Apellido(s)|Número de ID|Dirección de correo')
            for (col, data) in courseStudents.iterrows():
                students.append({"firstName": data.get('Nombre'), "lastName": data.get('Apellido(s)'), "email": data.get('Dirección de correo')})

            attendanceSesions = list()
            attendanceInfo = attendanceDataframe.filter(regex="\d{2} [a-zA-Z]{3} \d{4} \d{1,2}\.\d{2}[amAMpmPM]{2} Todos los estudiantes|Dirección de correo")
            for col in attendanceInfo:
                if col != 'Dirección de correo':
                    attendanceSesions.append(col.replace(" Todos los estudiantes", ""))
                


            courseContent = dataframe.filter(regex='Quiz|Assignment|Attendance|Cuestionario|Tarea|Asistencia')
            
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

            i = 0
            studentGradeList = list(dict())
            for student in students:
                studentActivities = dataframe.loc[dataframe['Dirección de correo'] == student['email']].filter(regex='Email address|Quiz|Assignment|Attendance|Dirección de correo|Cuestionario|Tarea|Asistencia')
                studentSessions = attendanceInfo.loc[attendanceInfo['Dirección de correo'] == student['email']].filter(regex="\d{2} [a-zA-Z]{3} \d{4} \d{1,2}\.\d{2}[amAMpmPM]{2} Todos los estudiantes|Dirección de correo")
                
                activityList = list(dict())
                for quiz in quizes:
                    studentGrade = studentActivities[f"{quiz['type']}:{quiz['name']} (Real)"]

                    if studentGrade[i] == '-':

                        activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': 0})
                    
                    else:
                    
                        activityList.append({'type': quiz['type'], 'name': quiz['name'], 'grade': studentGrade[i]})

                for attend in attendance:
                    studentGrade = studentSessions[f"{attend['sesion']} Todos los estudiantes"][i].split(" ")[0]

                    if studentGrade == 'P' or studentGrade == 'L':

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

            context = {
                'students': students,
                'quizList': quizes,
                'courseName': courseName,
                'teacher': username,
                'studentGrades': studentGradeList,
                'objectiveList': ast.literal_eval(objectiveList),
                'attendanceList': attendance,
                'assignmentList': assignments
            }

            return render(request, "confActivities.html", context=context)


    return render(request, "teacherPage.html")

@csrf_exempt
@xframe_options_exempt
def confWeigth(request):

    students = request.POST.get("students")
    courseName = request.POST.get("courseName").replace("/", "")
    teacher = request.POST.get('teacher')
    studentGrades = request.POST.get("studentGrades")
    objectiveList = request.POST.get("objectiveList")
    activitiesInfo = request.POST.get("activitiesInfo")


    return redirect(reverse("createCourse", kwargs={'activities': activitiesInfo, 'studentList': students, "courseName": courseName, 'teacher': teacher, 'studentGrades': studentGrades, 'objectiveList': objectiveList}))

