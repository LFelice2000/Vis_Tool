# Generated by Django 3.2.20 on 2024-01-09 13:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_alter_update_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='update',
            old_name='Teacher',
            new_name='teacher',
        ),
    ]
