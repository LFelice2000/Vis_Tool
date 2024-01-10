# Generated by Django 3.2.20 on 2024-01-09 13:05

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20240109_1100'),
    ]

    operations = [
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime(2024, 1, 9, 13, 5, 13, 506603))),
                ('Teacher', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='core.teacher')),
                ('course', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='core.course')),
            ],
        ),
    ]
