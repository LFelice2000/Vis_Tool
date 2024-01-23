# Generated by Django 3.2.20 on 2024-01-09 10:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20240108_1617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='objective',
        ),
        migrations.AddField(
            model_name='sesion',
            name='objective',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='core.objective'),
        ),
    ]