from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include

urlpatterns = [
    path("createCourse/<str:activities>/<str:studentList>/<str:courseName>/<str:teacher>/<str:studentGrades>/<str:objectiveList>/", views.createCourse, name="createCourse"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)