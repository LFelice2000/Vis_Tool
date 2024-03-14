import ast
import json

from core.models import Course, Sesion, Student, Quiz, Teacher, Grade, Objective, Assignment, Attendance, Update, GlobalScores, StudentScores

from django.db import IntegrityError
from django.db import transaction

def createCourse(activities, studentList, courseName, courseShortName, teacher, studentGrades, objectiveList, courseId, group):
    
    activitiesObj = ast.literal_eval(activities)
    studentsObj = ast.literal_eval(studentList)
    studentGradesObj = ast.literal_eval(studentGrades)
    objectiveListObj = ast.literal_eval(objectiveList)
    
    try:
        with transaction.atomic():
            course = Course(name=courseName, group=group)
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

                act = Attendance(course=course, weight=float(activity['weigth']))
                act.save()
            
            globalGradeAcum = {}
            for student in studentGradesObj:

                studentProgress = {}
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

                                if not act.objective.name in globalGradeAcum:
                                    globalGradeAcum[act.objective.name] = grade.grade * float(act.weight/100)
                                else:
                                    globalGradeAcum[act.objective.name] += grade.grade * float(act.weight/100)
                                
                                if not act.objective.name in studentProgress:
                                    studentProgress[act.objective.name] = grade.grade * float(act.weight/100)
                                else:
                                    studentProgress[act.objective.name] += grade.grade * float(act.weight/100)
                            
                        elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                grade = Grade(grade=activity['grade'])
                                grade.save()

                                grade.student.add(stu)
                                grade.course.add(course)

                                act.grade.add(grade)
                                act.save()

                                if not act.objective.name in globalGradeAcum:
                                    globalGradeAcum[act.objective.name] = grade.grade * float(act.weight/100)
                                else:
                                    globalGradeAcum[act.objective.name] += grade.grade * float(act.weight/100)

                                if not act.objective.name in studentProgress:
                                    studentProgress[act.objective.name] = grade.grade * float(act.weight/100)
                                else:
                                    studentProgress[act.objective.name] += grade.grade * float(act.weight/100)

                        elif activity['type'] == 'Asistencia':
                            
                            act = Attendance.objects.filter(course=course).first()

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

                                    if not objectiveName in globalGradeAcum:
                                        globalGradeAcum[objectiveName] = grade.grade * float(act.weight/100)
                                    else:
                                        globalGradeAcum[objectiveName] += grade.grade * float(act.weight/100)
                                    
                                    if not objectiveName in studentProgress:
                                        studentProgress[objectiveName] = grade.grade * float(act.weight/100)
                                    else:
                                        studentProgress[objectiveName] += grade.grade * float(act.weight/100)
                    
                    for objectiveName in studentProgress:
                        obj = Objective.objects.filter(name=objectiveName, course=course).first()
                        
                        if obj:

                            stuScore = StudentScores(percentage=round((float(studentProgress[objectiveName])*10), 2), objective=obj)
                            stuScore.save()

                            stuScore.student.add(stu)                      

            for objectiveName in globalGradeAcum:
                obj = Objective.objects.filter(name=objectiveName, course=course).first()
                numStudents = Student.objects.filter(course=course).all().count()
                if obj:

                    gloScore = GlobalScores(percentage=round((float(globalGradeAcum[objectiveName])/numStudents)*10, 2), objective=obj)
                    gloScore.save()
                    

    except Exception as e:
        
        return {"status": "error", "error": f"Error creating the course ({e})"}

    return {"status": "success"}

def updateCourse(activities, courseName, courseShortName, studentGrades, teacher, courseId, group):

    activitiesObj = ast.literal_eval(str(activities))
    studentGradesObj = ast.literal_eval(str(studentGrades))
    
    try:
        with transaction.atomic():
            
            course = Course.objects.filter(name=courseName, group=group).first()
            
            globalGradeAcum = {}
            for student in studentGradesObj:
                
                studentProgress = {}
                stu = Student.objects.filter(email=student['student'], course=course).first()

                if stu:
                    for activity in student['activities']:

                        if activity['type'] == 'Cuestionario':

                            act = Quiz.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(quiz__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    Grade.objects.filter(id=grade.id).update(grade=float(activity['grade']))

                                    if not act.objective.name in globalGradeAcum:
                                        globalGradeAcum[act.objective.name] = grade.grade * (act.weight/100)
                                    else:
                                        globalGradeAcum[act.objective.name] += grade.grade * (act.weight/100)

                                    if not act.objective.name in studentProgress:
                                        studentProgress[act.objective.name] = grade.grade * (act.weight/100)
                                    else:
                                        studentProgress[act.objective.name] += grade.grade * (act.weight/100)

                        elif activity['type'] == 'Tarea':

                            act = Assignment.objects.filter(name=activity['name'], course=course).first()
                            
                            if act:
                                
                                grade = Grade.objects.filter(assignment__id=act.id, student__id=stu.id).first()

                                if grade and grade.grade != activity['grade']:
                                    Grade.objects.filter(id=grade.id).update(grade=float(activity['grade']))
                                    
                                    if not act.objective.name in globalGradeAcum:
                                        globalGradeAcum[act.objective.name] = grade.grade * (act.weight/100)
                                    else:
                                        globalGradeAcum[act.objective.name] += grade.grade * (act.weight/100)
                                    
                                    if not act.objective.name in studentProgress:
                                        studentProgress[act.objective.name] = grade.grade * (act.weight/100)
                                    else:
                                        studentProgress[act.objective.name] += grade.grade * (act.weight/100)
                                        
                        
                        elif activity['type'] == 'Asistencia':
                            
                            act = Attendance.objects.filter(course=course).first()
                            
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
                                                
                                                if not sesion.objective.name in globalGradeAcum:
                                                    globalGradeAcum[sesion.objective.name] = grade.grade * (act.weight/100)
                                                else:
                                                    globalGradeAcum[sesion.objective.name] += grade.grade * (act.weight/100)
                                                
                                                if not sesion.objective.name in studentProgress:
                                                    studentProgress[sesion.objective.name] = grade.grade * (act.weight/100)
                                                else:
                                                    studentProgress[sesion.objective.name] += grade.grade * (act.weight/100)
                    for objectiveName in studentProgress:
                        obj = Objective.objects.filter(name=objectiveName, course=course).first()
                        
                        if obj:

                            stuScore = StudentScores.objects.filter(student=stu, objective=obj).first()

                            if stuScore:
                                StudentScores.objects.filter(student=stu, objective=obj).update(percentage=round((float(studentProgress[objectiveName])*10), 2))
                            else:
                                stuScore = StudentScores(percentage=round((float(studentProgress[objectiveName])*10), 2), objective=obj)
                                stuScore.save()

                                stuScore.student.add(stu)   

            for objectiveName in globalGradeAcum:
                obj = Objective.objects.filter(name=objectiveName, course=course).first()
                numStudents = Student.objects.filter(course=course).all().count()
                if obj:

                    gloScore = GlobalScores.objects.filter(objective=obj).first()
                    if gloScore:
                        GlobalScores.objects.filter(objective=obj).update(percentage=round((float(globalGradeAcum[objectiveName])/numStudents)*10, 2))
                    else:
                        gloScore = GlobalScores(percentage=round((float(globalGradeAcum[objectiveName])/numStudents)*10, 2), objective=obj)
                        gloScore.save()
             
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
        
        if course:
            return [t.email for t in Teacher.objects.filter(course=course)]
    
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
                
                if teacher:
                    teacher.course.add(course)

        except Exception as e:
            print(e)
            return None
    
    return None

def addStudentToCourse(student, courseName):

    course = Course.objects.filter(name=courseName).first()

    if course:

        stu = Student.objects.filter(email=student['mail']).first()

        if not stu:
            try:
                with transaction.atomic():

                    formatedName = ' '.join(e.capitalize() for e in student['name'].split(' '))
                    stu = Student(email=student['mail'], name=formatedName)
                    stu.save()

                    stu.course.add(course)
            except Exception as e:
                print(e)
                return None
        else:
            try:
                with transaction.atomic():

                    stu = Student.objects.filter(email=student['mail']).first()

                    if stu:
        
                        stu.course.add(course)
            except Exception as e:
                print(e)
                return None
    
    return None

def deleteTeacher(teacher, courseName):

    course = Course.objects.filter(name=courseName).first()

    if course:

        teacher = Teacher.objects.filter(email=teacher).first()

        if teacher:

            try:
                with transaction.atomic():
                    teacher.course.remove(course)
            except Exception as e:
                print(e)
                return None
            
            return True
    
    return None

def deleteStudent(student, courseName):

    course = Course.objects.filter(name=courseName).first()

    if course:

        stu = Student.objects.filter(email=student).first()

        if stu:

            try:
                with transaction.atomic():
                    stu.course.remove(course)
            except Exception as e:
                print(e)
                return None
            
            return True
    
    return None

def getGlobalScore(objective):

    return GlobalScores.objects.filter(objective=objective).first()

def getPersonalScores(objective, student):

    return StudentScores.objects.filter(student__id=student.id, objective=objective).first()

def getStudent(studentMail):

    return Student.objects.filter(email=studentMail).first()