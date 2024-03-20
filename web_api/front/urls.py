from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.visPage, name="index"),
    path("confNewCourse/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.confNewCourse, name="confNewCourse"),
    path("confPage/", views.confPage, name="confPage"),
    path("confWeigth/", views.confWeigth, name="confWeigth"),
    path("teacherAdmin/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.teacherPage, name="teacherAdmin"),
    path("teacherlanding/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>", views.teacherlanding, name="teacherLanding"),
    path("update/", views.update, name="update"),
    path("error/<str:error>", views.error, name='error'),
    path("manageTeacher/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.manageTeacher, name="manageTeacher"),
    path("manageStudents/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.manageStudent, name="manageStudent"),
    path("addTeacher/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.addTeacher, name="addTeacher"),
    path("addStudent/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.addStudent, name="addStudent"),
    path("removeTeacher/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.removeTeacher, name="removeTeacher"),
    path("removeStudent/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.removeStudent, name="removeStudent"),
    path("studentInfo/<str:courseName>/<str:courseShortName>/<str:teacherMail>/<str:courseId>/<int:group>", views.studentInfo, name="studentInfo"),
    path("core/", include("core.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)