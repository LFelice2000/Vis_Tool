# Generated by Django 3.2.20 on 2023-11-29 18:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_delete_activity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='grade',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.grade'),
        ),
    ]
