from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.visPage, name="index"),
    path("confPage/", views.confPage, name="confPage"),
    path("confWeigth/", views.confWeigth, name="confWeigth"),
    path("teacherAdmin/", views.teacherPage, name="teacherAdmin"),
    path("update/", views.update, name="update"),
    path("error/", views.error, name='error'),
    path("core/", include("core.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)