from django.contrib import admin
from selenium_bot import views
from django.urls import path


urlpatterns = [
    path("", views.testUp),
]