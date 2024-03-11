from django.db import models
from django.core.exceptions import ValidationError
import re
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.timezone import now

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    group = models.IntegerField(unique=True, default=-1)

class Teacher(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    email = models.CharField(max_length=200, unique=True)
    course = models.ManyToManyField(Course)

class Student(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200, unique=True)
    course = models.ManyToManyField(Course)

class Grade(models.Model):
    student = models.ManyToManyField(Student)
    course = models.ManyToManyField(Course)
    grade = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(10), MinValueValidator(0)], default=0)

class Objective(models.Model):
    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)

class Quiz(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=200)
    grade = models.ManyToManyField(Grade)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, default=None)
    weight = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)

class Assignment(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=200)
    grade = models.ManyToManyField(Grade)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, default=None)
    weight = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)

class Sesion(models.Model):
    name = models.CharField(max_length=100)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, default=None)
    grade = models.ManyToManyField(Grade)

class Attendance(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)
    sesions = models.ManyToManyField(Sesion)
    weight = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)

class Update(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, default=None)
    date = models.DateTimeField(default=now, editable=False)

class GlobalScores(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, default=None)
    percentage = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)

class StudentScores(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, default=None)
    student = models.ManyToManyField(Student)
    percentage = models.DecimalField(max_digits=4, decimal_places=2, validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)